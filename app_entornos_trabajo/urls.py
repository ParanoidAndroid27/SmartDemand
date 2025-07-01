from django.urls import path
from . import views

app_name = 'app_entornos_trabajo'

urlpatterns = [
    path('gestionar/', views.gestionar_entorno_trabajo, name='gestionar_entorno'),
    path('agregar-colaborador/', views.agregar_colaborador, name='agregar_colaborador'),
    path('seleccionar/', views.listar_y_seleccionar_entornos, name='listar_y_seleccionar_entornos'),
    path('activar/<int:entorno_id>/', views.activar_entorno_sesion, name='activar_entorno_sesion'),
]