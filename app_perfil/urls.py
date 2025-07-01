# filepath: c:\SmartDemand\app_perfil\urls.py
from django.urls import path
from . import views

app_name = 'app_perfil'
urlpatterns = [
    path('', views.perfil_view, name='perfil'),
    path('editar/', views.editar_perfil_view, name='editar_perfil'),
]