from django.contrib import admin
from .models import Especialidad, Cita, Recordatorio

@admin.register(Especialidad)
class EspecialidadAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'icono', 'activa']

@admin.register(Cita)
class CitaAdmin(admin.ModelAdmin):
    list_display = ['paciente', 'especialidad', 'fecha', 'hora', 'estado']
    list_filter = ['estado', 'especialidad']
    search_fields = ['paciente__nombre', 'medico']
    date_hierarchy = 'fecha'
    readonly_fields = ['creado_at', 'actualizado_at']

@admin.register(Recordatorio)
class RecordatorioAdmin(admin.ModelAdmin):
    list_display = ['cita', 'tipo', 'canal', 'enviado', 'enviado_at']
    list_filter = ['tipo', 'canal', 'enviado']
