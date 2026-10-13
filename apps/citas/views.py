"""DON VITAL - Vistas de Citas"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Cita, Especialidad
from .forms import CitaForm
from django.views.decorators.http import require_POST
from apps.pacientes.permisos import pacientes_de, puede_ver_paciente


@login_required
def dashboard(request):
    """Vista principal - dashboard según rol"""
    usuario = request.user

    hoy = timezone.localdate()
    pacientes = pacientes_de(usuario)
    ids_pacientes = list(pacientes.values_list('id', flat=True))
    ids_pacientes_tomas = ids_pacientes

    citas_hoy = Cita.objects.filter(
        paciente_id__in=ids_pacientes,
        fecha=hoy,
        estado__in=['programada', 'confirmada']
    ).select_related('paciente', 'especialidad').order_by('hora')

    citas_proximas = Cita.objects.filter(
        paciente_id__in=ids_pacientes,
        fecha__gt=hoy,
        estado__in=['programada', 'confirmada']
    ).select_related('paciente', 'especialidad').order_by('fecha', 'hora')[:10]

    from apps.notificaciones.models import Notificacion
    from apps.medicamentos.models import RegistroToma

    notifs_recientes = Notificacion.objects.filter(
        usuario=usuario, leida=False
    ).order_by('-creado_at')[:5]

    tomas_hoy = RegistroToma.objects.filter(
        fecha_programada=hoy,
        medicamento__paciente_id__in=ids_pacientes_tomas,
        medicamento__estado='activo',
    ).select_related('medicamento__paciente').order_by('hora_programada')

    return render(request, 'dashboard/index.html', {
        'citas_hoy': citas_hoy,
        'citas_proximas': citas_proximas,
        'pacientes': pacientes,
        'notifs_recientes': notifs_recientes,
        'tomas_hoy': tomas_hoy,
        'hoy': timezone.localtime(),
    })


@login_required
def lista_citas(request):
    usuario = request.user
    estado_filtro = request.GET.get('estado', '')

    ids_pacientes = list(pacientes_de(usuario).values_list('id', flat=True))
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

    if not puede_ver_paciente(usuario, cita.paciente):
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

    pacientes_disponibles = pacientes_de(usuario)

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

    if not puede_ver_paciente(usuario, cita.paciente):
        messages.error(request, 'No tienes permiso para editar esta cita.')
        return redirect('lista_citas')

    pacientes_disponibles = pacientes_de(usuario)
    form = CitaForm(request.POST or None, instance=cita, pacientes=pacientes_disponibles)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Cita actualizada correctamente.')
        return redirect('detalle_cita', pk=pk)

    return render(request, 'citas/form.html', {
        'form': form, 'titulo': 'Editar Cita', 'cita': cita
    })


@login_required
@require_POST
def confirmar_cita(request, pk):
    cita = get_object_or_404(Cita, pk=pk)
    if not puede_ver_paciente(request.user, cita.paciente):
        messages.error(request, 'No tienes acceso a esta cita.')
        return redirect('lista_citas')
    if cita.estado == Cita.ESTADO_PROGRAMADA:
        cita.confirmar(request.user)
        messages.success(request, f'✅ Cita de {cita.paciente.nombre} confirmada.')
    return redirect('detalle_cita', pk=pk)


@login_required
@require_POST
def cancelar_cita(request, pk):
    cita = get_object_or_404(Cita, pk=pk)
    if not puede_ver_paciente(request.user, cita.paciente):
        messages.error(request, 'No tienes acceso a esta cita.')
        return redirect('lista_citas')
    cita.cancelar()
    messages.warning(request, f'Cita cancelada.')
    return redirect('lista_citas')
