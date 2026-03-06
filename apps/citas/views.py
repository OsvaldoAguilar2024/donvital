"""DON VITAL - Vistas de Citas"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Cita, Especialidad
from .forms import CitaForm
from apps.pacientes.models import CuidadorPaciente


@login_required
def dashboard(request):
    """Vista principal - dashboard según rol"""
    usuario = request.user
    
    if usuario.rol == 'admin':
        citas_hoy = Cita.objects.filter(
            fecha=timezone.now().date(),
            estado__in=['programada', 'confirmada']
        ).select_related('paciente', 'especialidad').order_by('hora')
        citas_proximas = Cita.objects.filter(
            fecha__gt=timezone.now().date(),
            estado__in=['programada', 'confirmada']
        ).select_related('paciente', 'especialidad').order_by('fecha', 'hora')[:10]
        pacientes = None
    else:
        pacientes = usuario.get_pacientes()
        ids_pacientes = list(pacientes.values_list('id', flat=True))
        
        citas_hoy = Cita.objects.filter(
            paciente_id__in=ids_pacientes,
            fecha=timezone.now().date(),
            estado__in=['programada', 'confirmada']
        ).select_related('paciente', 'especialidad').order_by('hora')
        
        citas_proximas = Cita.objects.filter(
            paciente_id__in=ids_pacientes,
            fecha__gt=timezone.now().date(),
            estado__in=['programada', 'confirmada']
        ).select_related('paciente', 'especialidad').order_by('fecha', 'hora')[:10]
    
    from apps.notificaciones.models import Notificacion
    notifs_recientes = Notificacion.objects.filter(
        usuario=usuario, leida=False
    ).order_by('-creado_at')[:5]
    
    return render(request, 'dashboard/index.html', {
        'citas_hoy': citas_hoy,
        'citas_proximas': citas_proximas,
        'pacientes': pacientes,
        'notifs_recientes': notifs_recientes,
        'hoy': timezone.now(),
    })


@login_required
def lista_citas(request):
    usuario = request.user
    estado_filtro = request.GET.get('estado', '')
    
    if usuario.rol == 'admin':
        citas = Cita.objects.all()
    else:
        ids_pacientes = list(usuario.get_pacientes().values_list('id', flat=True))
        citas = Cita.objects.filter(paciente_id__in=ids_pacientes)
    
    if estado_filtro:
        citas = citas.filter(estado=estado_filtro)
    
    citas = citas.select_related('paciente', 'especialidad').order_by('-fecha', '-hora')
    
    return render(request, 'citas/lista.html', {
        'citas': citas,
        'estado_filtro': estado_filtro,
        'estados': Cita.ESTADOS,
    })


@login_required
def detalle_cita(request, pk):
    cita = get_object_or_404(Cita, pk=pk)
    usuario = request.user
    
    # Verificar acceso
    if usuario.rol != 'admin':
        if not CuidadorPaciente.objects.filter(
            usuario=usuario, paciente=cita.paciente, activo=True
        ).exists():
            messages.error(request, 'No tienes acceso a esta cita.')
            return redirect('lista_citas')
    
    recordatorios = cita.recordatorios.order_by('tipo')
    return render(request, 'citas/detalle.html', {
        'cita': cita,
        'recordatorios': recordatorios,
    })


@login_required
def crear_cita(request):
    usuario = request.user
    
    if usuario.rol == 'admin':
        from apps.pacientes.models import Paciente
        pacientes_disponibles = Paciente.objects.filter(activo=True)
    else:
        pacientes_disponibles = usuario.get_pacientes()
    
    if not pacientes_disponibles.exists():
        messages.warning(request, 'Primero debes registrar un paciente.')
        return redirect('crear_paciente')
    
    form = CitaForm(request.POST or None, pacientes=pacientes_disponibles)
    
    if request.method == 'POST' and form.is_valid():
        cita = form.save(commit=False)
        cita.creado_por = usuario
        cita.save()
        
        # Programar recordatorios
        try:
            from apps.notificaciones.tasks import programar_recordatorios_cita
            programar_recordatorios_cita(cita.id)
        except Exception:
            pass
        
        messages.success(request, f'Cita registrada para {cita.paciente.nombre} el {cita.fecha}.')
        return redirect('detalle_cita', pk=cita.pk)
    
    especialidades = Especialidad.objects.filter(activa=True)
    return render(request, 'citas/form.html', {
        'form': form,
        'titulo': 'Nueva Cita',
        'especialidades': especialidades,
    })


@login_required
def editar_cita(request, pk):
    cita = get_object_or_404(Cita, pk=pk)
    usuario = request.user
    
    if usuario.rol != 'admin':
        if not CuidadorPaciente.objects.filter(
            usuario=usuario, paciente=cita.paciente, activo=True
        ).exists():
            messages.error(request, 'No tienes permiso para editar esta cita.')
            return redirect('lista_citas')
    
    pacientes_disponibles = usuario.get_pacientes() if usuario.rol != 'admin' else None
    form = CitaForm(request.POST or None, instance=cita, pacientes=pacientes_disponibles)
    
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Cita actualizada correctamente.')
        return redirect('detalle_cita', pk=pk)
    
    return render(request, 'citas/form.html', {
        'form': form, 'titulo': 'Editar Cita', 'cita': cita
    })


@login_required
def confirmar_cita(request, pk):
    cita = get_object_or_404(Cita, pk=pk)
    if cita.estado == Cita.ESTADO_PROGRAMADA:
        cita.confirmar(request.user)
        messages.success(request, f'✅ Cita de {cita.paciente.nombre} confirmada.')
    return redirect('detalle_cita', pk=pk)


@login_required
def cancelar_cita(request, pk):
    cita = get_object_or_404(Cita, pk=pk)
    cita.cancelar()
    messages.warning(request, f'Cita cancelada.')
    return redirect('lista_citas')