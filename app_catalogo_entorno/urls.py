from django.shortcuts import render
from django.urls import path
from . import views

app_name = 'app_catalogo_entorno'

urlpatterns = [
    path('<int:entorno_id>/', views.catalogo_entorno, name='catalogo_entorno'),
    path('<int:entorno_id>/crear_producto/', views.crear_producto_entorno, name='crear_producto_entorno'),
    path('producto/<int:pk>/editar/', views.editar_producto_entorno, name='editar_producto_entorno'),
    path('producto/<int:pk>/eliminar/', views.eliminar_producto_entorno, name='eliminar_producto_entorno'),
]
