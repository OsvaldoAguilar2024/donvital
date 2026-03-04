from django.contrib import admin
from .models import Paciente, CuidadorPaciente

@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'eps', 'activo', 'creado_at']
    list_filter = ['activo', 'eps']
    search_fields = ['nombre', 'eps']
    readonly_fields = ['creado_at', 'actualizado_at']

@admin.register(CuidadorPaciente)
class CuidadorPacienteAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'paciente', 'rol', 'activo']
    list_filter = ['rol', 'activo']
