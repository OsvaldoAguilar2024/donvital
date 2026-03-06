from django.urls import path
from . import portal_views

urlpatterns = [
    path('', portal_views.portal_login, name='portal_login'),
    path('inicio/', portal_views.portal_paciente, name='portal_paciente'),
    path('emergencia/', portal_views.portal_emergencia, name='portal_emergencia'),
    path('salir/', portal_views.portal_salir, name='portal_salir'),
]
