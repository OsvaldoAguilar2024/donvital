from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Notificacion


@login_required
def lista_notificaciones(request):
    notifs = Notificacion.objects.filter(usuario=request.user).order_by('-creado_at')[:50]
    return render(request, 'base/notificaciones.html', {'notificaciones': notifs})


@login_required
def marcar_leida(request, pk):
    notif = get_object_or_404(Notificacion, pk=pk, usuario=request.user)
    notif.marcar_leida()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'ok': True})
    return redirect('notificaciones')


@login_required
def marcar_todas_leidas(request):
    Notificacion.objects.filter(usuario=request.user, leida=False).update(leida=True)
    return redirect('notificaciones')
