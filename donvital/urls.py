from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.usuarios.urls')),
    path('dashboard/', include('apps.citas.urls_dashboard')),
    path('pacientes/', include('apps.pacientes.urls')),
    path('citas/', include('apps.citas.urls')),
    path('medicamentos/', include('apps.medicamentos.urls')),
    path('notificaciones/', include('apps.notificaciones.urls')),
    path('suscripciones/', include('apps.suscripciones.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
