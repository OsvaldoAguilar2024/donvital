"""
DON VITAL - Vistas de Usuarios (Login OTP, Registro, Perfil)
"""
import random
import string
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import Usuario, OTPVerificacion
from django.utils import timezone; from datetime import timedelta
from .forms import (
    RegistroForm, TelefonoLoginForm, OTPVerificacionForm, PerfilForm
)
from apps.notificaciones.services import enviar_sms_otp


def generar_otp():
    return ''.join(random.choices(string.digits, k=6))


def login_view(request):
    """Paso 1: ingresar teléfono"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    form = TelefonoLoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        telefono = form.cleaned_data['telefono']
        
        try:
            usuario = Usuario.objects.get(telefono=telefono, is_active=True)
        except Usuario.DoesNotExist:
            messages.error(request, 'Número de teléfono no registrado.')
            return render(request, 'usuarios/login.html', {'form': form})
        
        # Generar y guardar OTP
        codigo = generar_otp()
        OTPVerificacion.objects.filter(telefono=telefono, usado=False).update(usado=True)
        otp = OTPVerificacion.objects.create(telefono=telefono, codigo=codigo, expira_at=timezone.now() + timedelta(minutes=10))
        
        # Enviar SMS (en desarrollo muestra en consola)
        enviado = enviar_sms_otp(telefono, codigo)
        
        request.session['otp_telefono'] = telefono
        request.session['otp_id'] = otp.id
        
        if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
            return JsonResponse({'ok': True, 'debug_code': codigo if settings.DEBUG else None})
        
        return redirect('verificar_otp')
    
    return render(request, 'usuarios/login.html', {'form': form})


def verificar_otp(request):
    """Paso 2: verificar código OTP"""
    telefono = request.session.get('otp_telefono')
    otp_id = request.session.get('otp_id')
    
    if not telefono or not otp_id:
        return redirect('login')
    
    form = OTPVerificacionForm(request.POST or None)
    
    if request.method == 'POST' and form.is_valid():
        codigo_ingresado = form.cleaned_data['codigo']
        
        try:
            otp = OTPVerificacion.objects.get(id=otp_id, telefono=telefono)
        except OTPVerificacion.DoesNotExist:
            messages.error(request, 'Código inválido. Intenta de nuevo.')
            return redirect('login')
        
        otp.intentos += 1
        otp.save()
        
        if not otp.es_valido():
            messages.error(request, 'El código expiró o es inválido. Solicita uno nuevo.')
            return redirect('login')
        
        if otp.codigo != codigo_ingresado:
            messages.error(request, f'Código incorrecto. Intentos: {otp.intentos}/3')
            return render(request, 'usuarios/verificar_otp.html', {
                'form': form, 'telefono': telefono
            })
        
        # OTP correcto
        otp.usado = True
        otp.save()
        
        usuario = Usuario.objects.get(telefono=telefono)
        usuario.ultimo_acceso = timezone.now()
        usuario.save()
        
        login(request, usuario)
        
        del request.session['otp_telefono']
        del request.session['otp_id']
        
        messages.success(request, f'¡Bienvenido/a, {usuario.nombre}!')
        return redirect(request.GET.get('next', 'dashboard'))
    
    return render(request, 'usuarios/verificar_otp.html', {
        'form': form,
        'telefono': telefono
    })


def registro_view(request):
    """Registro de nuevo usuario"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    form = RegistroForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        usuario = form.save()
        messages.success(
            request,
            f'¡Cuenta creada! Ahora inicia sesión con tu número {usuario.telefono}.'
        )
        return redirect('login')
    
    return render(request, 'usuarios/registro.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def perfil_view(request):
    form = PerfilForm(request.POST or None, request.FILES or None, instance=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Perfil actualizado correctamente.')
        return redirect('perfil')
    return render(request, 'usuarios/perfil.html', {'form': form})


def context_processors(request):
    return {}
