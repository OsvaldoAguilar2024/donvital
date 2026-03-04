from django.db import models
from django.utils import timezone
from apps.usuarios.models import Usuario


class Plan(models.Model):
    nombre = models.CharField(max_length=100)
    precio_usd = models.DecimalField(max_digits=8, decimal_places=2)
    precio_cop = models.IntegerField()
    max_pacientes = models.PositiveIntegerField(default=2)
    max_cuidadores = models.PositiveIntegerField(default=1)
    descripcion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Plan'

    def __str__(self):
        return f'{self.nombre} (${self.precio_usd} USD)'


class Suscripcion(models.Model):
    ESTADO_TRIAL = 'trial'
    ESTADO_ACTIVA = 'activa'
    ESTADO_VENCIDA = 'vencida'
    ESTADO_CANCELADA = 'cancelada'
    ESTADOS = [
        (ESTADO_TRIAL, 'Período gratuito'),
        (ESTADO_ACTIVA, 'Activa'),
        (ESTADO_VENCIDA, 'Vencida'),
        (ESTADO_CANCELADA, 'Cancelada'),
    ]

    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='suscripciones')
    plan = models.ForeignKey(Plan, on_delete=models.SET_NULL, null=True)
    estado = models.CharField(max_length=15, choices=ESTADOS, default=ESTADO_TRIAL)
    meses_gratis = models.PositiveIntegerField(default=0)
    fecha_inicio = models.DateField(default=timezone.now)
    fecha_fin = models.DateField(null=True, blank=True)
    codigo_referido = models.CharField(max_length=20, blank=True)
    creado_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Suscripción'

    def __str__(self):
        return f'{self.usuario.nombre} - {self.plan} - {self.estado}'

    @property
    def esta_activa(self):
        if self.estado in [self.ESTADO_TRIAL, self.ESTADO_ACTIVA]:
            if self.fecha_fin:
                return self.fecha_fin >= timezone.now().date()
            return True
        return False
