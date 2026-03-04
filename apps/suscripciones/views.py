from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Suscripcion, Plan


@login_required
def mi_plan(request):
    suscripcion = Suscripcion.objects.filter(
        usuario=request.user
    ).order_by('-creado_at').first()
    
    planes = Plan.objects.filter(activo=True)
    
    return render(request, 'suscripciones/mi_plan.html', {
        'suscripcion': suscripcion,
        'planes': planes,
    })