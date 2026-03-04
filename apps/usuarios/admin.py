from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, OTPVerificacion

@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ['telefono', 'nombre', 'rol', 'is_active', 'creado_at']
    list_filter = ['rol', 'is_active']
    search_fields = ['telefono', 'nombre']
    ordering = ['-creado_at']
    fieldsets = (
        (None, {'fields': ('telefono', 'password')}),
        ('Info', {'fields': ('nombre', 'email', 'rol', 'foto')}),
        ('Preferencias', {'fields': ('fuente_grande', 'alto_contraste', 'notif_push', 'notif_sms')}),
        ('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = ((None, {'fields': ('telefono', 'nombre', 'rol', 'password1', 'password2')}),)

@admin.register(OTPVerificacion)
class OTPAdmin(admin.ModelAdmin):
    list_display = ['telefono', 'codigo', 'usado', 'creado_at', 'expira_at']
    readonly_fields = ['creado_at']
