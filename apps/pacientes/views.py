"""DON VITAL - Vistas de Pacientes"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Paciente, CuidadorPaciente
from .forms import PacienteForm
from .permisos import pacientes_de, puede_ver_paciente


@login_required
def lista_pacientes(request):
    return render(request, 'pacientes/lista.html', {'pacientes': pacientes_de(request.user)})


@login_required
def detalle_paciente(request, pk):
    paciente = get_object_or_404(Paciente, pk=pk, activo=True)
    if not puede_ver_paciente(request.user, paciente):
        messages.error(request, 'No tienes acceso a este paciente.')
        return redirect('lista_pacientes')
    citas_proximas = paciente.citas.filter(estado__in=['programada', 'confirmada']).order_by('fecha', 'hora')[:5]
    cuidadores = CuidadorPaciente.objects.filter(paciente=paciente, activo=True).select_related('usuario')
    return render(request, 'pacientes/detalle.html', {
        'paciente': paciente,
        'citas_proximas': citas_proximas,
        'cuidadores': cuidadores,
    })


@login_required
def crear_paciente(request):
    form = PacienteForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        paciente = form.save()
        CuidadorPaciente.objects.create(
            usuario=request.user, paciente=paciente, rol='principal'
        )
        messages.success(request, f'Paciente {paciente.nombre} registrado correctamente.')
        return redirect('detalle_paciente', pk=paciente.pk)
    return render(request, 'pacientes/form.html', {'form': form, 'titulo': 'Nuevo Paciente'})


@login_required
def editar_paciente(request, pk):
    paciente = get_object_or_404(Paciente, pk=pk, activo=True)
    if not puede_ver_paciente(request.user, paciente):
        messages.error(request, 'No tienes acceso a este paciente.')
        return redirect('lista_pacientes')
    form = PacienteForm(request.POST or None, request.FILES or None, instance=paciente)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Información del paciente actualizada.')
        return redirect('detalle_paciente', pk=pk)
    return render(request, 'pacientes/form.html', {'form': form, 'titulo': 'Editar Paciente', 'paciente': paciente})
