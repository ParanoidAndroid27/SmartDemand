from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from app_cargar_productos.models import Producto
from .forms import ProductoForm

@login_required
def lista_productos(request):
    entorno_id = request.session.get('entorno_activo_id')
    if not entorno_id:
        return redirect('app_entornos_trabajo:listar_y_seleccionar_entornos')
    
    # Muestra productos del entorno activo O productos creados por el usuario.
    # Esta lógica ya es correcta según tu requisito.
    productos_entorno = Producto.objects.filter(entorno_id=entorno_id)
    productos_usuario = Producto.objects.filter(creado_por=request.user)
    productos = (productos_entorno | productos_usuario).distinct().order_by('-destacado', '-fecha_registro')
    
    return render(request, 'app_gestion_productos/lista_productos.html',
                  {'productos': productos})

@login_required
def detalle_producto(request, pk):
    entorno_id = request.session.get('entorno_activo_id')
    # Permite ver si el producto es del entorno activo O fue creado por el usuario.
    producto = get_object_or_404(Producto, Q(entorno_id=entorno_id) | Q(creado_por=request.user), pk=pk)
    return render(request, 'app_gestion_productos/detalle_producto.html', {'producto': producto})

@login_required
def editar_producto(request, pk):
    entorno_id = request.session.get('entorno_activo_id')
    # Permite editar si el producto es del entorno activo O fue creado por el usuario.
    producto = get_object_or_404(Producto, Q(entorno_id=entorno_id) | Q(creado_por=request.user), pk=pk)
    
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES, instance=producto, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('app_gestion_productos:lista_productos')
    else:
        form = ProductoForm(instance=producto, user=request.user)
    return render(request, 'app_gestion_productos/editar_producto.html',
                  {'form': form, 'producto': producto})

@login_required
def eliminar_producto(request, pk):
    entorno_id = request.session.get('entorno_activo_id')
    # Permite eliminar si el producto es del entorno activo O fue creado por el usuario.
    producto = get_object_or_404(Producto, Q(entorno_id=entorno_id) | Q(creado_por=request.user), pk=pk)
    
    if request.method == 'POST':
        producto.delete()
        return redirect('app_gestion_productos:lista_productos')
    return render(request, 'app_gestion_productos/eliminar_producto.html',
                  {'producto': producto})

def buscar_productos(request):
    query = request.GET.get('q', '')
    entorno_id = request.session.get('entorno_activo_id')
    productos = []
    if query and entorno_id:
        # La búsqueda también debe reflejar la misma lógica de acceso.
        productos = Producto.objects.filter(
            Q(nombre__icontains=query),
            Q(entorno_id=entorno_id) | Q(creado_por=request.user)
        ).distinct()
    return render(request, 'app_gestion_productos/resultados_busqueda.html', {
        'productos': productos,
        'query': query,
    })

def autocomplete_productos(request):
    q = request.GET.get('q', '')
    entorno_id = request.session.get('entorno_activo_id')
    resultados = []
    if q and entorno_id:
        # El autocompletado también debe reflejar la misma lógica.
        productos = Producto.objects.filter(
            Q(nombre__icontains=q),
            Q(entorno_id=entorno_id) | Q(creado_por=request.user)
        ).distinct()[:8]
        resultados = [{'id': p.id, 'nombre': p.nombre} for p in productos]
    return JsonResponse(resultados, safe=False)
