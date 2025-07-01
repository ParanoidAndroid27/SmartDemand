from django.urls import path
from . import views

app_name = 'app_gestion_productos'

urlpatterns = [
    path('', views.lista_productos, name='lista_productos'),
    path('producto/<int:pk>/', views.detalle_producto, name='detalle_producto'),
    path('producto/<int:pk>/editar/', views.editar_producto, name='editar_producto'),
    path('producto/<int:pk>/eliminar/', views.eliminar_producto, name='eliminar_producto'),
    path('buscar-productos/', views.buscar_productos, name='buscar_productos'),
    path('autocomplete-productos/', views.autocomplete_productos, name='autocomplete_productos'),
]
