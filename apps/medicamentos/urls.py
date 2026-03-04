from django.urls import path
from . import views
urlpatterns = [
    path('', views.lista_medicamentos, name='lista_medicamentos'),
    path('hoy/', views.tomas_del_dia, name='tomas_del_dia'),
    path('nuevo/', views.crear_medicamento, name='crear_medicamento'),
    path('nuevo/paciente/<int:paciente_id>/', views.crear_medicamento, name='crear_medicamento_paciente'),
    path('<int:pk>/', views.detalle_medicamento, name='detalle_medicamento'),
    path('<int:pk>/editar/', views.editar_medicamento, name='editar_medicamento'),
    path('toma/<int:toma_id>/confirmar/', views.confirmar_toma, name='confirmar_toma'),
    path('toma/<int:toma_id>/omitir/', views.omitir_toma, name='omitir_toma'),
]
