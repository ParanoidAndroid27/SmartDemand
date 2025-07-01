
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from app_cargar_productos.models import Producto
from .forms import ProductoForm

@login_required
def lista_productos(request):
    entorno_id = request.session.get('entorno_activo_id')
    if not entorno_id:
        return redirect('app_entornos_trabajo:listar_y_seleccionar_entornos')
    # Productos del entorno activo
    productos_entorno = Producto.objects.filter(entorno_id=entorno_id)
    # Productos almacenados por el usuario (en cualquier entorno)
    productos_usuario = Producto.objects.filter(creado_por=request.user)
    # Unir ambos QuerySets y eliminar duplicados
    productos = (productos_entorno | productos_usuario).distinct()
    return render(request, 'app_gestion_productos/lista_productos.html',
                  {'productos': productos})

@login_required
def detalle_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    return render(request, 'app_gestion_productos/detalle_producto.html', {'producto': producto})

@login_required
def editar_producto(request, pk):
    entorno_id = request.session.get('entorno_activo_id')
    producto = get_object_or_404(Producto, pk=pk, entorno_id=entorno_id)
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES, instance=producto, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('app_gestion_productos:lista_productos')
    else:
        form = ProductoForm(instance=producto, user=request.user)
    return render(request, 'app_gestion_productos/editar_producto.html',
                  {'form': form})

@login_required
def eliminar_producto(request, pk):
    entorno_id = request.session.get('entorno_activo_id')
    producto = get_object_or_404(Producto, pk=pk, entorno_id=entorno_id)
    if request.method == 'POST':
        producto.delete()
        return redirect('app_gestion_productos:lista_productos')
    return render(request, 'app_gestion_productos/eliminar_producto.html',
                  {'producto': producto})

def buscar_productos(request):
    query = request.GET.get('q', '')
    productos = Producto.objects.filter(nombre__icontains=query) if query else []
    return render(request, 'app_gestion_productos/resultados_busqueda.html', {
        'productos': productos,
        'query': query,
    })

def autocomplete_productos(request):
    q = request.GET.get('q', '')
    productos = Producto.objects.filter(nombre__icontains=q)[:8]
    resultados = [{'id': p.id, 'nombre': p.nombre} for p in productos]
    return JsonResponse(resultados, safe=False)
