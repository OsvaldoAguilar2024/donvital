from django.db import models
from apps.usuarios.models import Usuario


class Notificacion(models.Model):
    TIPO_RECORDATORIO = 'recordatorio'
    TIPO_ALERTA = 'alerta'
    TIPO_INFO = 'info'
    TIPOS = [
        (TIPO_RECORDATORIO, 'Recordatorio'),
        (TIPO_ALERTA, 'Alerta'),
        (TIPO_INFO, 'Información'),
    ]

    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='notificaciones')
    tipo = models.CharField(max_length=15, choices=TIPOS, default=TIPO_INFO)
    titulo = models.CharField(max_length=200)
    mensaje = models.TextField()
    leida = models.BooleanField(default=False)
    leida_at = models.DateTimeField(null=True, blank=True)
    url_accion = models.CharField(max_length=200, blank=True)
    creado_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'
        ordering = ['-creado_at']

    def __str__(self):
        return f'{self.titulo} → {self.usuario.nombre}'

    def marcar_leida(self):
        from django.utils import timezone
        if not self.leida:
            self.leida = True
            self.leida_at = timezone.now()
            self.save(update_fields=['leida', 'leida_at'])


class LogAuditoria(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, related_name='logs')
    accion = models.CharField(max_length=100)
    tabla_afectada = models.CharField(max_length=50, blank=True)
    objeto_id = models.IntegerField(null=True, blank=True)
    detalles = models.JSONField(default=dict, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    creado_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Log de Auditoría'
        verbose_name_plural = 'Logs de Auditoría'
        ordering = ['-creado_at']

    def __str__(self):
        return f'{self.accion} - {self.usuario} - {self.creado_at:%d/%m/%Y %H:%M}'
