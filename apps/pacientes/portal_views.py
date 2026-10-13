"""DON VITAL - Portal del Paciente (cédula + PIN)."""
from datetime import timedelta

from django.core.cache import cache
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST

MAX_INTENTOS_PIN = 5
BLOQUEO_MINUTOS = 15
MAX_INTENTOS_POR_IP = 20          # por hora, para frenar barridos de cédulas
EMERGENCIA_CADA_MINUTOS = 5

ERROR_GENERICO = 'Cédula o PIN incorrectos.'


def _ip(request):
    fwd = request.META.get('HTTP_X_FORWARDED_FOR', '')
    return (fwd.split(',')[0].strip() if fwd else request.META.get('REMOTE_ADDR', '')) or 'desconocida'


def _contar_intento_ip(request) -> int:
    clave = f'portal:ip:{_ip(request)}'
    cache.add(clave, 0, 3600)
    try:
        return cache.incr(clave)
    except ValueError:
        cache.set(clave, 1, 3600)
        return 1


@csrf_protect
def portal_login(request):
    """Acceso del paciente: cédula + PIN que le asigna su cuidador."""
    if request.method != 'POST':
        return render(request, 'paciente/login.html')

    if _contar_intento_ip(request) > MAX_INTENTOS_POR_IP:
        return render(request, 'paciente/login.html',
                      {'error': 'Demasiados intentos. Espera un momento e inténtalo de nuevo.'}, status=429)

    cedula = request.POST.get('cedula', '').strip().replace(' ', '').replace('.', '')
    pin = request.POST.get('pin', '').strip()
    if not cedula or not pin:
        return render(request, 'paciente/login.html', {'error': 'Ingresa tu cédula y tu PIN.'})

    from apps.pacientes.models import Paciente
    paciente = Paciente.objects.filter(cedula=cedula, activo=True).first()
    ahora = timezone.now()

    if paciente and paciente.portal_bloqueado_hasta and paciente.portal_bloqueado_hasta > ahora:
        return render(request, 'paciente/login.html', {
            'error': f'Acceso bloqueado por intentos fallidos. Intenta en {BLOQUEO_MINUTOS} minutos '
                     f'o pídele a tu cuidador que te asigne un PIN nuevo.'
        }, status=429)

    if not paciente or not paciente.check_pin(pin):
        if paciente:
            paciente.portal_intentos_fallidos += 1
            if paciente.portal_intentos_fallidos >= MAX_INTENTOS_PIN:
                paciente.portal_bloqueado_hasta = ahora + timedelta(minutes=BLOQUEO_MINUTOS)
                paciente.portal_intentos_fallidos = 0
            paciente.save(update_fields=['portal_intentos_fallidos', 'portal_bloqueado_hasta'])
        else:
            # Igualar el tiempo de respuesta para no revelar si la cédula existe
            from django.contrib.auth.hashers import make_password
            make_password(pin)
        return render(request, 'paciente/login.html', {'error': ERROR_GENERICO})

    paciente.portal_intentos_fallidos = 0
    paciente.portal_bloqueado_hasta = None
    paciente.save(update_fields=['portal_intentos_fallidos', 'portal_bloqueado_hasta'])

    request.session.cycle_key()
    request.session['paciente_id'] = paciente.id
    request.session['paciente_nombre'] = paciente.nombre
    request.session.set_expiry(60 * 60 * 12)  # 12 horas
    return redirect('portal_paciente')


def _paciente_de_sesion(request):
    from apps.pacientes.models import Paciente
    paciente_id = request.session.get('paciente_id')
    if not paciente_id:
        return None
    return Paciente.objects.filter(id=paciente_id, activo=True).first()


def portal_paciente(request):
    """Interfaz principal del paciente — medicamentos del día + emergencia."""
    paciente = _paciente_de_sesion(request)
    if not paciente:
        request.session.flush()
        return redirect('portal_login')

    from apps.medicamentos.models import RegistroToma
    hoy = timezone.localdate()
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


def _coordenada(valor, limite):
    try:
        v = float(valor)
    except (TypeError, ValueError):
        return None
    return round(v, 6) if -limite <= v <= limite else None


@csrf_protect
@require_POST
def portal_emergencia(request):
    """Botón de emergencia — avisa a los cuidadores. Máximo un envío cada 5 minutos."""
    paciente = _paciente_de_sesion(request)
    if not paciente:
        return redirect('portal_login')

    from apps.pacientes.models import CuidadorPaciente
    from apps.notificaciones.services import enviar_sms, crear_notificacion_interna

    contexto = {'paciente': paciente, 'tomas': [], 'hoy': timezone.localdate()}

    clave = f'portal:emergencia:{paciente.id}'
    if not cache.add(clave, 1, EMERGENCIA_CADA_MINUTOS * 60):
        contexto['emergencia_enviada'] = True
        contexto['emergencia_repetida'] = True
        return render(request, 'paciente/portal.html', contexto)

    lat = _coordenada(request.POST.get('latitud'), 90)
    lon = _coordenada(request.POST.get('longitud'), 180)
    if lat is not None and lon is not None:
        mensaje_sms = (f'EMERGENCIA Don Vital: {paciente.nombre} necesita ayuda urgente. '
                       f'Ubicación: https://maps.google.com/?q={lat},{lon}')
    else:
        mensaje_sms = (f'EMERGENCIA Don Vital: {paciente.nombre} necesita ayuda urgente. '
                       f'No se pudo obtener ubicación. Comunícate de inmediato.')

    cuidadores = CuidadorPaciente.objects.filter(paciente=paciente, activo=True).select_related('usuario')
    for rel in cuidadores:
        crear_notificacion_interna(
            usuario=rel.usuario,
            titulo=f'🚨 EMERGENCIA: {paciente.nombre}',
            mensaje=mensaje_sms,
            tipo='alerta',
            url='/dashboard/',
        )
        if rel.usuario.telefono:
            enviar_sms(rel.usuario.telefono, mensaje_sms)

    contexto['emergencia_enviada'] = True
    return render(request, 'paciente/portal.html', contexto)


def portal_salir(request):
    """Cierra la sesión del paciente."""
    request.session.flush()
    return redirect('portal_login')
