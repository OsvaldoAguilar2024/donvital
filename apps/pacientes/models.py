from django.db import models
from apps.usuarios.models import Usuario


class Paciente(models.Model):
    nombre = models.CharField(max_length=150, verbose_name='Nombre completo')
    cedula = models.CharField(max_length=20, blank=True, verbose_name='Cédula de ciudadanía')
    fecha_nacimiento = models.DateField(null=True, blank=True, verbose_name='Fecha de nacimiento')
    telefono = models.CharField(max_length=20, blank=True)
    eps = models.CharField(max_length=100, blank=True, verbose_name='EPS')
    numero_afiliacion = models.CharField(max_length=50, blank=True, verbose_name='N° afiliación EPS')
    grupo_sanguineo = models.CharField(max_length=10, blank=True, verbose_name='Grupo sanguíneo')
    alergias = models.TextField(blank=True, verbose_name='Alergias conocidas')
    condiciones = models.TextField(blank=True, verbose_name='Condiciones médicas')
    medicamentos_actuales = models.TextField(blank=True, verbose_name='Medicamentos actuales')
    contacto_emergencia = models.CharField(max_length=150, blank=True)
    telefono_emergencia = models.CharField(max_length=20, blank=True)
    foto = models.ImageField(upload_to='pacientes/fotos/', blank=True, null=True)
    foto_carnet_eps = models.ImageField(upload_to='pacientes/carnets/', blank=True, null=True)
    activo = models.BooleanField(default=True)
    notas = models.TextField(blank=True)
    creado_at = models.DateTimeField(auto_now_add=True)
    actualizado_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Paciente'
        verbose_name_plural = 'Pacientes'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

    @property
    def edad(self):
        if not self.fecha_nacimiento:
            return None
        from django.utils import timezone
        hoy = timezone.now().date()
        return hoy.year - self.fecha_nacimiento.year - (
            (hoy.month, hoy.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day)
        )


class CuidadorPaciente(models.Model):
    ROL_PRINCIPAL = 'principal'
    ROL_EXTRA = 'extra'
    ROLES = [
        (ROL_PRINCIPAL, 'Cuidador Principal'),
        (ROL_EXTRA, 'Cuidador Adicional'),
    ]
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='cuidadores_pacientes')
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='cuidadores')
    rol = models.CharField(max_length=15, choices=ROLES, default=ROL_PRINCIPAL)
    activo = models.BooleanField(default=True)
    creado_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Cuidador - Paciente'
        unique_together = ['usuario', 'paciente']

    def __str__(self):
        return f'{self.usuario.nombre} cuida a {self.paciente.nombre}'
