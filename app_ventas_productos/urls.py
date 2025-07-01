from django.urls import path
from . import views

app_name = 'app_ventas_productos'

urlpatterns = [
    path('registrar/', views.registrar_venta, name='registrar_venta'),
    path('cargar_csv/', views.cargar_ventas_csv, name='cargar_ventas_csv'),
    path('listar/', views.listar_ventas, name='listar_ventas'),  # <--- NUEVA RUTA
]
