from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UsuarioManager(BaseUserManager):
    def create_user(self, telefono, nombre, password=None, **extra):
        if not telefono:
            raise ValueError('El teléfono es obligatorio')
        user = self.model(telefono=telefono, nombre=nombre, **extra)
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, telefono, nombre, password, **extra):
        extra.setdefault('rol', 'admin')
        extra.setdefault('is_staff', True)
        extra.setdefault('is_superuser', True)
        return self.create_user(telefono, nombre, password, **extra)


class Usuario(AbstractBaseUser, PermissionsMixin):
    ROL_PACIENTE = 'paciente'
    ROL_CUIDADOR_PRINCIPAL = 'cuidador_principal'
    ROL_CUIDADOR_EXTRA = 'cuidador_extra'
    ROL_ADMIN = 'admin'
    ROLES = [
        (ROL_PACIENTE, 'Paciente'),
        (ROL_CUIDADOR_PRINCIPAL, 'Cuidador Principal'),
        (ROL_CUIDADOR_EXTRA, 'Cuidador Adicional'),
        (ROL_ADMIN, 'Administrador'),
    ]

    telefono = models.CharField(max_length=20, unique=True, verbose_name='Teléfono')
    nombre = models.CharField(max_length=150, verbose_name='Nombre completo')
    email = models.EmailField(blank=True, verbose_name='Correo electrónico')
    rol = models.CharField(max_length=25, choices=ROLES, default=ROL_CUIDADOR_PRINCIPAL)
    foto = models.ImageField(upload_to='usuarios/fotos/', blank=True, null=True)

    # Preferencias de accesibilidad
    fuente_grande = models.BooleanField(default=False, verbose_name='Fuente grande')
    alto_contraste = models.BooleanField(default=False, verbose_name='Alto contraste')

    # Notificaciones
    notif_push = models.BooleanField(default=True)
    notif_sms = models.BooleanField(default=True)
    fcm_token = models.TextField(blank=True, verbose_name='Token FCM')

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    creado_at = models.DateTimeField(auto_now_add=True)

    objects = UsuarioManager()

    USERNAME_FIELD = 'telefono'
    REQUIRED_FIELDS = ['nombre']

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return f'{self.nombre} ({self.telefono})'

    def get_pacientes(self):
        from apps.pacientes.models import Paciente
        ids = self.cuidadores_pacientes.filter(activo=True).values_list('paciente_id', flat=True)
        return Paciente.objects.filter(id__in=ids)


class OTPVerificacion(models.Model):
    telefono = models.CharField(max_length=20)
    codigo = models.CharField(max_length=6)
    intentos = models.PositiveIntegerField(default=0)
    usado = models.BooleanField(default=False)
    creado_at = models.DateTimeField(auto_now_add=True)
    expira_at = models.DateTimeField()

    class Meta:
        verbose_name = 'Verificación OTP'

    def __str__(self):
        return f'OTP {self.telefono}'
    
    def es_valido(self):
        from django.utils import timezone
        return (
            not self.usado and
            self.intentos < 3 and
            self.expira_at > timezone.now()
        )
