def notificaciones_no_leidas(request):
    count = 0
    if request.user.is_authenticated:
        try:
            from apps.notificaciones.models import Notificacion
            count = Notificacion.objects.filter(usuario=request.user, leida=False).count()
        except Exception:
            pass
    return {'notifs_count': count}
