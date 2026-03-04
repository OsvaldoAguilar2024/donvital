from django.contrib import admin
from .models import Notificacion, LogAuditoria

@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'tipo', 'titulo', 'leida', 'creado_at']
    list_filter = ['tipo', 'leida']
    search_fields = ['usuario__nombre', 'titulo']
    readonly_fields = ['creado_at', 'leida_at']
    ordering = ['-creado_at']

@admin.register(LogAuditoria)
class LogAuditoriaAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'accion', 'tabla_afectada', 'ip', 'creado_at']
    list_filter = ['accion']
    readonly_fields = ['creado_at']
    ordering = ['-creado_at']
