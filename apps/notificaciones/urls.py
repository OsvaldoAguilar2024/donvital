from django.urls import path
from . import views
urlpatterns = [
    path('', views.lista_notificaciones, name='lista_notificaciones'),
    path('<int:pk>/leer/', views.marcar_leida, name='marcar_notificacion_leida'),
    path('leer-todas/', views.marcar_todas_leidas, name='marcar_todas_leidas'),
]
