from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
import logging
import secrets

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.core.cache import cache

logger = logging.getLogger(__name__)

OTP_MINUTOS = 10
OTP_MAX_ENVIOS = 3            # por número, cada 15 minutos
PASSWORD_MAX_FALLOS = 5       # por número, cada 15 minutos
VENTANA_SEG = 15 * 60
ERROR_LOGIN = 'Número o contraseña incorrectos.'


def generar_otp() -> str:
    return f'{secrets.randbelow(1_000_000):06d}'


def _contador(clave: str) -> int:
    return cache.get(clave, 0)


def _sumar(clave: str):
    cache.add(clave, 0, VENTANA_SEG)
    try:
        cache.incr(clave)
    except ValueError:
        cache.set(clave, 1, VENTANA_SEG)


def login_view(request):
    """Login con dos opciones: contraseña o código por SMS."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method != 'POST':
        return render(request, 'usuarios/login.html')

    from apps.notificaciones.services import normalizar_telefono, enviar_sms_otp
    from .models import Usuario, OTPVerificacion

    telefono_raw = request.POST.get('telefono', '').strip()
    metodo = request.POST.get('metodo', 'password')
    if not telefono_raw:
        messages.error(request, 'Ingresa tu número de teléfono.')
        return render(request, 'usuarios/login.html')
    telefono = normalizar_telefono(telefono_raw)
    usuario = Usuario.objects.filter(telefono=telefono, is_active=True).first()

    if metodo == 'password':
        clave = f'login:fallos:{telefono}'
        if _contador(clave) >= PASSWORD_MAX_FALLOS:
            messages.error(request, 'Demasiados intentos. Espera 15 minutos o entra con código por SMS.')
            return render(request, 'usuarios/login.html', {'telefono': telefono_raw}, status=429)
        password = request.POST.get('password', '')
        if usuario and usuario.check_password(password):
            cache.delete(clave)
            login(request, usuario)
            messages.success(request, f'¡Bienvenido, {usuario.nombre}!')
            return redirect('dashboard')
        if not usuario:
            make_password(password)  # mismo tiempo de respuesta exista o no el número
        _sumar(clave)
        messages.error(request, ERROR_LOGIN)
        return render(request, 'usuarios/login.html', {'telefono': telefono_raw, 'mostrar_password': True})

    # --- Código por SMS ---
    clave_envios = f'otp:envios:{telefono}'
    if _contador(clave_envios) >= OTP_MAX_ENVIOS:
        messages.error(request, 'Ya pediste varios códigos. Espera 15 minutos e inténtalo de nuevo.')
        return render(request, 'usuarios/login.html', {'telefono': telefono_raw}, status=429)
    _sumar(clave_envios)

    if usuario:
        codigo = generar_otp()
        OTPVerificacion.objects.filter(telefono=telefono, usado=False).update(usado=True)
        OTPVerificacion.objects.create(
            telefono=telefono,
            codigo=make_password(codigo),
            expira_at=timezone.now() + timedelta(minutes=OTP_MINUTOS),
        )
        enviado = enviar_sms_otp(telefono, codigo)
        if not enviado:
            logger.error('No se pudo enviar el código por SMS a %s', telefono[-4:].rjust(len(telefono), '*'))
        if settings.DEBUG and not settings.TWILIO_ACCOUNT_SID:
            # Solo en desarrollo local, nunca en producción
            messages.info(request, f'[Desarrollo] Código: {codigo}')

    # Mismo mensaje exista o no la cuenta, para no revelar qué números están registrados
    messages.success(request, 'Si el número está registrado, te enviamos un código por SMS.')
    request.session['otp_telefono'] = telefono
    return redirect('verificar_otp')


def verificar_otp(request):
    telefono = request.session.get('otp_telefono')
    if not telefono:
        return redirect('login')

    if request.method == 'POST':
        from .models import Usuario, OTPVerificacion
        codigo = request.POST.get('codigo', '').strip()
        otp = OTPVerificacion.objects.filter(telefono=telefono, usado=False).order_by('-creado_at').first()
        usuario = Usuario.objects.filter(telefono=telefono, is_active=True).first()

        if otp and usuario and otp.es_valido() and codigo.isdigit() and otp.verificar(codigo):
            otp.usado = True
            otp.save(update_fields=['usado'])
            del request.session['otp_telefono']
            login(request, usuario)
            messages.success(request, f'¡Bienvenido, {usuario.nombre}!')
            return redirect('dashboard')

        if otp:
            otp.intentos += 1
            otp.save(update_fields=['intentos'])
            if otp.intentos >= otp.MAX_INTENTOS:
                otp.usado = True
                otp.save(update_fields=['usado'])
                del request.session['otp_telefono']
                messages.error(request, 'Demasiados intentos. Pide un código nuevo.')
                return redirect('login')
        messages.error(request, 'Código incorrecto o expirado.')

    return render(request, 'usuarios/verificar_otp.html', {'telefono': telefono})


def registro_view(request):
    from .forms import RegistroForm
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            usuario = form.save(commit=False)
            password = form.cleaned_data.get('password')
            if password:
                usuario.set_password(password)
            usuario.save()
            messages.success(request, '¡Cuenta creada! Ya puedes iniciar sesión.')
            return redirect('login')
    else:
        form = RegistroForm()

    return render(request, 'usuarios/registro.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def perfil_view(request):
    from .forms import PerfilForm
    if request.method == 'POST':
        form = PerfilForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil actualizado.')
    else:
        form = PerfilForm(instance=request.user)
    return render(request, 'usuarios/perfil.html', {'form': form})
