from django.db import models
from django.utils import timezone
from apps.pacientes.models import Paciente
from apps.usuarios.models import Usuario


class Especialidad(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    icono = models.CharField(max_length=10, default='🏥')
    activa = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Especialidad'
        verbose_name_plural = 'Especialidades'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Cita(models.Model):
    ESTADO_PROGRAMADA = 'programada'
    ESTADO_CONFIRMADA = 'confirmada'
    ESTADO_COMPLETADA = 'completada'
    ESTADO_CANCELADA = 'cancelada'
    ESTADO_PERDIDA = 'perdida'
    ESTADOS = [
        (ESTADO_PROGRAMADA, 'Programada'),
        (ESTADO_CONFIRMADA, 'Confirmada'),
        (ESTADO_COMPLETADA, 'Completada'),
        (ESTADO_CANCELADA, 'Cancelada'),
        (ESTADO_PERDIDA, 'Perdida'),
    ]

    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='citas')
    especialidad = models.ForeignKey(Especialidad, on_delete=models.SET_NULL, null=True, blank=True)
    medico = models.CharField(max_length=150, blank=True, verbose_name='Nombre del médico')
    fecha = models.DateField(verbose_name='Fecha de la cita')
    hora = models.TimeField(verbose_name='Hora de la cita')
    lugar = models.CharField(max_length=200, blank=True, verbose_name='Lugar / IPS / Clínica')
    direccion = models.CharField(max_length=250, blank=True)
    estado = models.CharField(max_length=15, choices=ESTADOS, default=ESTADO_PROGRAMADA)
    documentos_requeridos = models.TextField(blank=True, verbose_name='Documentos a llevar')
    notas = models.TextField(blank=True)
    creado_por = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, related_name='citas_creadas')
    creado_at = models.DateTimeField(auto_now_add=True)
    actualizado_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Cita'
        verbose_name_plural = 'Citas'
        ordering = ['fecha', 'hora']

    def __str__(self):
        esp = self.especialidad.nombre if self.especialidad else 'Cita'
        return f'{esp} - {self.paciente.nombre} - {self.fecha}'

    @property
    def es_futura(self):
        from datetime import datetime
        ahora = timezone.now()
        cita_dt = timezone.make_aware(datetime.combine(self.fecha, self.hora))
        return cita_dt > ahora

    @property
    def es_hoy(self):
        return self.fecha == timezone.now().date()


class Recordatorio(models.Model):
    TIPO_72H = '72h'
    TIPO_24H = '24h'
    TIPO_2H = '2h'
    TIPO_POST = 'post'
    TIPOS = [
        (TIPO_72H, '72 horas antes'),
        (TIPO_24H, '24 horas antes'),
        (TIPO_2H, '2 horas antes'),
        (TIPO_POST, 'Post cita (2h después)'),
    ]
    CANAL_PUSH = 'push'
    CANAL_SMS = 'sms'
    CANAL_WHATSAPP = 'whatsapp'
    CANALES = [
        (CANAL_PUSH, 'Push Notification'),
        (CANAL_SMS, 'SMS'),
        (CANAL_WHATSAPP, 'WhatsApp'),
    ]

    cita = models.ForeignKey(Cita, on_delete=models.CASCADE, related_name='recordatorios')
    tipo = models.CharField(max_length=5, choices=TIPOS)
    canal = models.CharField(max_length=10, choices=CANALES, default=CANAL_PUSH)
    enviado = models.BooleanField(default=False)
    enviado_at = models.DateTimeField(null=True, blank=True)
    error = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Recordatorio'
        unique_together = ['cita', 'tipo', 'canal']

    def __str__(self):
        return f'{self.get_tipo_display()} - {self.cita}'
