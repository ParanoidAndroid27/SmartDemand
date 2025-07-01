from django.urls import path
from . import views

app_name = 'app_cargar_productos'

urlpatterns = [
    path('agregar/', views.agregar_producto, name='agregar_producto'),
    path('cargar_csv/', views.cargar_csv, name='cargar_csv'),

]