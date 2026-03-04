from django.contrib import admin
from .models import Medicamento, RegistroToma, HistorialMedicamento

@admin.register(Medicamento)
class MedicamentoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'paciente', 'dosis', 'frecuencia_tipo', 'estado', 'stock_actual']
    list_filter = ['estado', 'frecuencia_tipo']
    search_fields = ['nombre', 'paciente__nombre']
    readonly_fields = ['creado_at', 'actualizado_at']

@admin.register(RegistroToma)
class RegistroTomaAdmin(admin.ModelAdmin):
    list_display = ['medicamento', 'fecha_programada', 'hora_programada', 'estado', 'confirmado_por']
    list_filter = ['estado', 'fecha_programada']
    date_hierarchy = 'fecha_programada'

@admin.register(HistorialMedicamento)
class HistorialAdmin(admin.ModelAdmin):
    list_display = ['medicamento', 'usuario', 'accion', 'creado_at']
    readonly_fields = ['creado_at']
