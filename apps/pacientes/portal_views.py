"""DON VITAL - Portal del Paciente (acceso público por teléfono)"""
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_protect
from django.utils import timezone
from django.contrib import messages


def normalizar_telefono(telefono: str) -> list:
    """Retorna variantes del teléfono para buscar en DB."""
    tel = telefono.strip().replace(' ', '').replace('-', '')
    variantes = [tel]
    if tel.startswith('+57'):
        variantes.append(tel[3:])
    elif tel.startswith('57') and len(tel) == 12:
        variantes.append(tel[2:])
        variantes.append('+' + tel)
    elif len(tel) == 10 and tel.startswith('3'):
        variantes.append('+57' + tel)
        variantes.append('57' + tel)
    return variantes


@csrf_protect
def portal_login(request):
    """Página de acceso del paciente — solo pide teléfono."""
    if request.method == 'POST':
        telefono = request.POST.get('telefono', '').strip()
        if not telefono:
            return render(request, 'paciente/login.html', {'error': 'Ingresa tu número de celular.'})

        from apps.pacientes.models import Paciente
        variantes = normalizar_telefono(telefono)
        paciente = Paciente.objects.filter(
            telefono__in=variantes, activo=True
        ).first()

        if not paciente:
            return render(request, 'paciente/login.html', {
                'error': 'No encontramos ese número. Pídele a tu cuidador que lo registre.'
            })

        # Guardar en sesión (sin usuario Django)
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

    # Construir mensaje
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

    # Notificar a todos los cuidadores
    cuidadores = CuidadorPaciente.objects.filter(
        paciente=paciente, activo=True
    ).select_related('usuario')

    for rel in cuidadores:
        usuario = rel.usuario
        # Notificación interna
        crear_notificacion_interna(
            usuario=usuario,
            titulo=f'🚨 EMERGENCIA: {paciente.nombre}',
            mensaje=mensaje_sms,
            tipo='alerta',
            url='/dashboard/',
        )
        # SMS
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
