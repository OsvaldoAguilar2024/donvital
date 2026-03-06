"""DON VITAL - Portal del Paciente (acceso público por cédula)"""
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_protect
from django.utils import timezone


@csrf_protect
def portal_login(request):
    """Página de acceso del paciente — solo pide cédula."""
    if request.method == 'POST':
        cedula = request.POST.get('cedula', '').strip().replace(' ', '').replace('.', '')
        if not cedula:
            return render(request, 'paciente/login.html', {'error': 'Ingresa tu número de cédula.'})

        from apps.pacientes.models import Paciente
        paciente = Paciente.objects.filter(cedula=cedula, activo=True).first()

        if not paciente:
            return render(request, 'paciente/login.html', {
                'error': 'No encontramos esa cédula. Pídele a tu cuidador que la registre.'
            })

        request.session['paciente_id'] = paciente.id
        request.session['paciente_nombre'] = paciente.nombre
        return redirect('portal_paciente')

    return render(request, 'paciente/login.html')


def portal_paciente(request):
    """Interfaz principal del paciente — medicamentos del día + emergencia."""
    paciente_id = request.session.get('paciente_id')
    if not paciente_id:
        return redirect('portal_login')

    from apps.pacientes.models import Paciente
    from apps.medicamentos.models import RegistroToma

    try:
        paciente = Paciente.objects.get(id=paciente_id, activo=True)
    except Paciente.DoesNotExist:
        del request.session['paciente_id']
        return redirect('portal_login')

    hoy = timezone.now().date()
    tomas = RegistroToma.objects.filter(
        fecha_programada=hoy,
        medicamento__paciente=paciente,
        medicamento__estado='activo',
    ).select_related('medicamento').order_by('hora_programada')

    return render(request, 'paciente/portal.html', {
        'paciente': paciente,
        'tomas': tomas,
        'hoy': hoy,
    })


@csrf_protect
def portal_emergencia(request):
    """Procesa el botón de emergencia — envía SMS a todos los cuidadores."""
    if request.method != 'POST':
        return redirect('portal_paciente')

    paciente_id = request.session.get('paciente_id')
    if not paciente_id:
        return redirect('portal_login')

    from apps.pacientes.models import Paciente, CuidadorPaciente
    from apps.notificaciones.services import enviar_sms, crear_notificacion_interna

    try:
        paciente = Paciente.objects.get(id=paciente_id, activo=True)
    except Paciente.DoesNotExist:
        return redirect('portal_login')

    latitud = request.POST.get('latitud', '')
    longitud = request.POST.get('longitud', '')

    if latitud and longitud:
        maps_url = f'https://maps.google.com/?q={latitud},{longitud}'
        mensaje_sms = (
            f'🚨 EMERGENCIA Don Vital: {paciente.nombre} necesita ayuda urgente. '
            f'Ubicación: {maps_url}'
        )
    else:
        mensaje_sms = (
            f'🚨 EMERGENCIA Don Vital: {paciente.nombre} necesita ayuda urgente. '
            f'No se pudo obtener ubicación. Comunícate de inmediato.'
        )

    cuidadores = CuidadorPaciente.objects.filter(
        paciente=paciente, activo=True
    ).select_related('usuario')

    for rel in cuidadores:
        usuario = rel.usuario
        crear_notificacion_interna(
            usuario=usuario,
            titulo=f'🚨 EMERGENCIA: {paciente.nombre}',
            mensaje=mensaje_sms,
            tipo='alerta',
            url='/dashboard/',
        )
        if usuario.telefono:
            try:
                enviar_sms(usuario.telefono, mensaje_sms)
            except Exception:
                pass

    return render(request, 'paciente/portal.html', {
        'paciente': paciente,
        'tomas': [],
        'hoy': timezone.now().date(),
        'emergencia_enviada': True,
    })


def portal_salir(request):
    """Cierra la sesión del paciente."""
    request.session.flush()
    return redirect('portal_login')
