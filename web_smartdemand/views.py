from django.shortcuts import render
from app_cargar_productos.models import Producto

def principal_page(request): # <-- Asegúrate de que este es el nombre de la función
    if request.user.is_authenticated:
        productos_destacados = Producto.objects.filter(destacado=True, creado_por=request.user)
    else:
        productos_destacados = Producto.objects.none()
    context = {
        'productos_destacados': productos_destacados
    }
    return render(request, 'web_smartdemand/Principal_Page.html', context)


