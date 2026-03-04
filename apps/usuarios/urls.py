from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.login_view, name='home'),
    path('usuarios/login/', views.login_view, name='login'),
    path('usuarios/logout/', views.logout_view, name='logout'),
    path('usuarios/otp/', views.verificar_otp, name='verificar_otp'),
    path('usuarios/registro/', views.registro_view, name='registro'),
    path('usuarios/perfil/', views.perfil_view, name='perfil'),
]
