from django.urls import path
from . import views
urlpatterns = [
    path('mi-plan/', views.mi_plan, name='mi_plan'),
]
