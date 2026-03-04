from django.urls import path
from . import views
urlpatterns = [
    path('', views.lista_pacientes, name='lista_pacientes'),
    path('nuevo/', views.crear_paciente, name='crear_paciente'),
    path('<int:pk>/', views.detalle_paciente, name='detalle_paciente'),
    path('<int:pk>/editar/', views.editar_paciente, name='editar_paciente'),
]
