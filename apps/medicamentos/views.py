"""DON VITAL - Vistas del módulo Medicamentos"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from .models import Medicamento, RegistroToma, HistorialMedicamento
from .forms import MedicamentoForm, ConfirmarTomaForm
from apps.pacientes.models import Paciente, CuidadorPaciente


def _verificar_acceso_paciente(request, paciente):
    """Verifica que el usuario tenga acceso al paciente."""
    if request.user.rol == 'admin':
        return True
    return CuidadorPaciente.objects.filter(
        usuario=request.user, paciente=paciente, activo=True
    ).exists()


@login_required
def lista_medicamentos(request):
    """Lista todos los medicamentos de los pacientes del cuidador."""
    if request.user.rol == 'admin':
        medicamentos = Medicamento.objects.select_related('paciente').order_by('paciente__nombre', 'nombre')
    else:
        ids_pacientes = list(request.user.get_pacientes().values_list('id', flat=True))
        medicamentos = Medicamento.objects.filter(
            paciente_id__in=ids_pacientes
        ).select_related('paciente').order_by('paciente__nombre', 'nombre')

    # Agrupar por paciente
    por_paciente = {}
    for med in medicamentos:
        key = med.paciente
        if key not in por_paciente:
            por_paciente[key] = []
        por_paciente[key].append(med)

    # Alertas del día
    hoy = timezone.now().date()
    alertas = {
        'stock_bajo': [m for m in medicamentos if m.stock_bajo],
        'receta_vencida': [m for m in medicamentos if m.receta_vencida],
        'receta_vence_pronto': [m for m in medicamentos if m.receta_vence_pronto and not m.receta_vencida],
        'medicamento_vencido': [m for m in medicamentos if m.medicamento_vencido],
    }

    return render(request, 'medicamentos/lista.html', {
        'por_paciente': por_paciente,
        'alertas': alertas,
        'total': medicamentos.count(),
    })


@login_required
def detalle_medicamento(request, pk):
    med = get_object_or_404(Medicamento, pk=pk)
    if not _verificar_acceso_paciente(request, med.paciente):
        messages.error(request, 'No tienes acceso a este medicamento.')
        return redirect('lista_medicamentos')

    hoy = timezone.now().date()
    tomas_hoy = RegistroToma.objects.filter(
        medicamento=med, fecha_programada=hoy
    ).order_by('hora_programada')

    # Historial de tomas últimos 7 días
    desde = hoy - timezone.timedelta(days=7)
    tomas_semana = RegistroToma.objects.filter(
        medicamento=med, fecha_programada__gte=desde
    ).order_by('-fecha_programada', '-hora_programada')

    historial = HistorialMedicamento.objects.filter(
        medicamento=med
    ).select_related('usuario').order_by('-creado_at')[:10]

    return render(request, 'medicamentos/detalle.html', {
        'med': med,
        'tomas_hoy': tomas_hoy,
        'tomas_semana': tomas_semana,
        'historial': historial,
        'hoy': hoy,
        'confirmar_form': ConfirmarTomaForm(),
    })


@login_required
def crear_medicamento(request, paciente_id=None):
    if request.user.rol == 'admin':
        pacientes_disponibles = Paciente.objects.filter(activo=True)
    else:
        pacientes_disponibles = request.user.get_pacientes()

    paciente_inicial = None
    if paciente_id:
        paciente_inicial = get_object_or_404(Paciente, pk=paciente_id)
        if not _verificar_acceso_paciente(request, paciente_inicial):
            messages.error(request, 'No tienes acceso a este paciente.')
            return redirect('lista_medicamentos')

    form = MedicamentoForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        med = form.save(commit=False)
        med.paciente = paciente_inicial or get_object_or_404(Paciente, pk=request.POST.get('paciente'))
        med.registrado_por = request.user
        med.save()

        # Registrar en historial
        HistorialMedicamento.objects.create(
            medicamento=med,
            usuario=request.user,
            accion='Medicamento registrado',
            detalle=f'Registrado por {request.user.nombre}'
        )

        # Generar tomas del día si el medicamento ya inició
        if med.fecha_inicio <= timezone.now().date():
            try:
                from .tasks import generar_registros_toma_diarios
                generar_registros_toma_diarios.delay()
            except Exception:
                pass

        messages.success(request, f'💊 Medicamento {med.nombre} registrado para {med.paciente.nombre}.')
        return redirect('detalle_medicamento', pk=med.pk)

    return render(request, 'medicamentos/form.html', {
        'form': form,
        'titulo': 'Nuevo Medicamento',
        'pacientes': pacientes_disponibles,
        'paciente_inicial': paciente_inicial,
    })


@login_required
def editar_medicamento(request, pk):
    med = get_object_or_404(Medicamento, pk=pk)
    if not _verificar_acceso_paciente(request, med.paciente):
        messages.error(request, 'No tienes acceso a este medicamento.')
        return redirect('lista_medicamentos')

    datos_anteriores = {
        'dosis': med.dosis,
        'frecuencia_tipo': med.get_frecuencia_tipo_display(),
        'estado': med.get_estado_display(),
    }

    form = MedicamentoForm(request.POST or None, request.FILES or None, instance=med)
    if form.is_valid():
        med_actualizado = form.save()

        # Registrar cambios en historial
        cambios = []
        if datos_anteriores['dosis'] != med_actualizado.dosis:
            cambios.append(f'Dosis: {datos_anteriores["dosis"]} → {med_actualizado.dosis}')
        if datos_anteriores['estado'] != med_actualizado.get_estado_display():
            cambios.append(f'Estado: {datos_anteriores["estado"]} → {med_actualizado.get_estado_display()}')

        HistorialMedicamento.objects.create(
            medicamento=med_actualizado,
            usuario=request.user,
            accion='Medicamento actualizado',
            detalle=', '.join(cambios) if cambios else 'Actualización general'
        )

        messages.success(request, f'Medicamento {med.nombre} actualizado.')
        return redirect('detalle_medicamento', pk=pk)

    return render(request, 'medicamentos/form.html', {
        'form': form,
        'titulo': f'Editar: {med.nombre}',
        'med': med,
    })


@login_required
def confirmar_toma(request, toma_id):
    """Confirmar que el paciente tomó el medicamento."""
    toma = get_object_or_404(RegistroToma, pk=toma_id)
    if not _verificar_acceso_paciente(request, toma.medicamento.paciente):
        return JsonResponse({'ok': False, 'error': 'Sin acceso'}, status=403)

    if request.method == 'POST':
        form = ConfirmarTomaForm(request.POST)
        if form.is_valid():
            toma.confirmar_toma(request.user, form.cleaned_data.get('notas', ''))
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'ok': True, 'estado': '✅ Tomado'})
            messages.success(request, f'✅ Toma de {toma.medicamento.nombre} confirmada.')
            return redirect('detalle_medicamento', pk=toma.medicamento.pk)

    return redirect('detalle_medicamento', pk=toma.medicamento.pk)


@login_required
def omitir_toma(request, toma_id):
    """Marcar una toma como omitida."""
    toma = get_object_or_404(RegistroToma, pk=toma_id)
    if not _verificar_acceso_paciente(request, toma.medicamento.paciente):
        return JsonResponse({'ok': False, 'error': 'Sin acceso'}, status=403)

    if request.method == 'POST':
        notas = request.POST.get('notas', '')
        toma.marcar_omitido(request.user, notas)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'ok': True, 'estado': '❌ Omitido'})
        messages.warning(request, f'Toma de {toma.medicamento.nombre} marcada como omitida.')
        return redirect('detalle_medicamento', pk=toma.medicamento.pk)

    return redirect('lista_medicamentos')


@login_required
def tomas_del_dia(request):
    """Vista del día: todas las tomas programadas para hoy de todos los pacientes."""
    hoy = timezone.now().date()

    if request.user.rol == 'admin':
        tomas = RegistroToma.objects.filter(fecha_programada=hoy)
    else:
        ids_pacientes = list(request.user.get_pacientes().values_list('id', flat=True))
        tomas = RegistroToma.objects.filter(
            fecha_programada=hoy,
            medicamento__paciente_id__in=ids_pacientes
        )

    tomas = tomas.select_related(
        'medicamento__paciente', 'confirmado_por'
    ).order_by('hora_programada')

    pendientes = tomas.filter(estado__in=['pendiente', 'retrasado']).count()
    tomadas = tomas.filter(estado='tomado').count()
    omitidas = tomas.filter(estado='omitido').count()

    return render(request, 'medicamentos/tomas_dia.html', {
        'tomas': tomas,
        'hoy': hoy,
        'pendientes': pendientes,
        'tomadas': tomadas,
        'omitidas': omitidas,
        'confirmar_form': ConfirmarTomaForm(),
    })
