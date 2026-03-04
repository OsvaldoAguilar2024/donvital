from django.contrib import admin
from .models import Plan, Suscripcion

@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'precio_usd', 'precio_cop', 'max_pacientes', 'activo']

@admin.register(Suscripcion)
class SuscripcionAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'plan', 'estado', 'fecha_inicio', 'fecha_fin']
    list_filter = ['estado', 'plan']
    readonly_fields = ['creado_at']
