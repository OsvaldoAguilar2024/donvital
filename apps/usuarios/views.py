from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
import random
import logging

logger = logging.getLogger(__name__)


def generar_otp():
    return str(random.randint(100000, 999999))


def login_view(request):
    """Login con dos opciones: contraseña o OTP por SMS"""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        telefono = request.POST.get('telefono', '').strip()
        metodo = request.POST.get('metodo', 'password')  # 'password' o 'otp'
        
        if not telefono:
            messages.error(request, 'Ingresa tu número de teléfono.')
            return render(request, 'usuarios/login.html')

        from .models import Usuario
        try:
            usuario = Usuario.objects.get(telefono=telefono)
        except Usuario.DoesNotExist:
            messages.error(request, 'Número no registrado. ¿Ya tienes una cuenta?')
            return render(request, 'usuarios/login.html')

        if metodo == 'password':
            # Login con contraseña
            password = request.POST.get('password', '')
            if usuario.check_password(password):
                login(request, usuario)
                messages.success(request, f'¡Bienvenido, {usuario.nombre}!')
                return redirect('dashboard')
            else:
                messages.error(request, 'Contraseña incorrecta.')
                return render(request, 'usuarios/login.html', {'telefono': telefono, 'mostrar_password': True})

        else:
            # Login con OTP
            from .models import OTPVerificacion
            import importlib
            
            otp_codigo = generar_otp()
            expira_at = timezone.now() + timedelta(minutes=10)
            
            OTPVerificacion.objects.create(
                usuario=usuario,
                codigo=otp_codigo,
                expira_at=expira_at
            )

            # Enviar SMS
            try:
                from django.conf import settings
                from twilio.rest import Client
                client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
                client.messages.create(
                    body=f'Don Vital: Tu código de acceso es {otp_codigo}. Válido por 10 minutos.',
                    from_=settings.TWILIO_PHONE_NUMBER,
                    to=telefono
                )
                messages.success(request, f'Código enviado a {telefono}')
            except Exception as e:
                logger.error(f"Error enviando SMS: {e}")
                messages.warning(request, f'[DEV] Código OTP: {otp_codigo}')

            request.session['otp_telefono'] = telefono
            return redirect('verificar_otp')

    return render(request, 'usuarios/login.html')


def verificar_otp(request):
    telefono = request.session.get('otp_telefono')
    if not telefono:
        return redirect('login')

    if request.method == 'POST':
        codigo = request.POST.get('codigo', '').strip()
        from .models import Usuario, OTPVerificacion

        try:
            usuario = Usuario.objects.get(telefono=telefono)
            otp = OTPVerificacion.objects.filter(
                usuario=usuario,
                codigo=codigo,
                usado=False
            ).order_by('-creado_at').first()

            if otp and otp.es_valido():
                otp.usado = True
                otp.save()
                del request.session['otp_telefono']
                login(request, usuario)
                messages.success(request, f'¡Bienvenido, {usuario.nombre}!')
                return redirect('dashboard')
            else:
                messages.error(request, 'Código incorrecto o expirado.')
        except Usuario.DoesNotExist:
            messages.error(request, 'Usuario no encontrado.')

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
