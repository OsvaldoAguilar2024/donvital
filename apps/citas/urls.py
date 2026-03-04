from django.urls import path
from . import views
urlpatterns = [
    path('', views.lista_citas, name='lista_citas'),
    path('nueva/', views.crear_cita, name='crear_cita'),
    path('<int:pk>/', views.detalle_cita, name='detalle_cita'),
    path('<int:pk>/editar/', views.editar_cita, name='editar_cita'),
    path('<int:pk>/confirmar/', views.confirmar_cita, name='confirmar_cita'),
    path('<int:pk>/cancelar/', views.cancelar_cita, name='cancelar_cita'),
]
