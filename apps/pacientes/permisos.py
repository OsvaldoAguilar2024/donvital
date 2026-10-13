"""DON VITAL - Reglas de acceso en un solo lugar.

Regla general: un usuario solo ve y modifica pacientes de los que es
cuidador activo. Solo un superusuario (creado por consola, nunca desde el
registro público) ve todo.
"""
from django.core.exceptions import PermissionDenied


def es_admin(usuario) -> bool:
    """Administrador real = superusuario. El campo `rol` no da privilegios."""
    return bool(usuario and usuario.is_authenticated and usuario.is_superuser)


def pacientes_de(usuario):
    """Pacientes activos que el usuario puede ver."""
    from .models import Paciente
    if es_admin(usuario):
        return Paciente.objects.filter(activo=True)
    return usuario.get_pacientes().filter(activo=True)


def puede_ver_paciente(usuario, paciente) -> bool:
    if es_admin(usuario):
        return True
    from .models import CuidadorPaciente
    return CuidadorPaciente.objects.filter(
        usuario=usuario, paciente=paciente, activo=True
    ).exists()


def exigir_acceso(usuario, paciente):
    """Lanza 403 si el usuario no tiene acceso al paciente."""
    if not puede_ver_paciente(usuario, paciente):
        raise PermissionDenied('No tienes acceso a este paciente.')
