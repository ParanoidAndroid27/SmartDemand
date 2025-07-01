# filepath: c:\SmartDemand\app_catalogo_entorno\views.py
from django.db import models
from django.contrib.auth.models import User
from app_cargar_productos.models import Producto # <--- IMPORTA Producto
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib import messages
from app_entornos_trabajo.models import EntornoTrabajo # <--- CORRECTO
from app_cargar_productos.models import Producto    # <--- CORRECTO
from .forms import ProductoForm # Asumiendo que tienes un ProductoForm en esta app o lo importas de app_cargar_productos

@login_required
def catalogo_entorno(request, entorno_id):
    entorno_actual = get_object_or_404(EntornoTrabajo, pk=entorno_id)
    if request.user != entorno_actual.administrador:
        return HttpResponseForbidden("No eres el administrador de este entorno.")

    if request.method == 'POST':
        if 'agregar_productos' in request.POST:
            productos_ids_a_agregar = request.POST.getlist('productos_a_agregar')
            if productos_ids_a_agregar:
                productos_seleccionados = Producto.objects.filter(
                    creado_por=request.user,
                    entorno__isnull=True,
                    id__in=productos_ids_a_agregar
                )
                
                count = 0
                for producto in productos_seleccionados:
                    producto.entorno = entorno_actual
                    producto.save()
                    count += 1
                if count > 0:
                    messages.success(request, f"{count} producto(s) añadido(s) al catálogo del entorno.")
                else:
                    messages.warning(request, "No se seleccionaron productos válidos para añadir o ya estaban asignados.")
            else:
                messages.warning(request, "No seleccionaste ningún producto para añadir.")
            return redirect('app_catalogo_entorno:catalogo_entorno', entorno_id=entorno_id)

    productos_en_catalogo = Producto.objects.filter(entorno=entorno_actual)
    productos_disponibles_para_agregar = Producto.objects.filter(
        creado_por=request.user, 
        entorno__isnull=True
    ).exclude(id__in=productos_en_catalogo.values_list('id', flat=True))

    context = {
        'entorno': entorno_actual,
        'productos': productos_en_catalogo,  # <--- renombrado a 'productos'
        'productos_disponibles_para_agregar': productos_disponibles_para_agregar,
        'page_title': f"Catálogo del Entorno: {entorno_actual.nombre or entorno_actual.administrador.username}"
    }
    return render(request, 'app_catalogo_entorno/catalogo_entorno.html', context)

@login_required
def crear_producto_entorno(request, entorno_id):
    entorno_actual = get_object_or_404(EntornoTrabajo, pk=entorno_id)
    if request.user != entorno_actual.administrador:
        return HttpResponseForbidden("No eres el administrador de este entorno.")
    
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES) # Usa el ProductoForm que tengas definido
        if form.is_valid():
            producto_nuevo = form.save(commit=False)
            producto_nuevo.entorno = entorno_actual
            # Si tu ProductoForm no guarda creado_por, y quieres que sea el admin del entorno:
            if not producto_nuevo.creado_por:
                 producto_nuevo.creado_por = request.user # O entorno_actual.administrador
            producto_nuevo.save()
            messages.success(request, f"Producto '{producto_nuevo.nombre}' creado y añadido al catálogo.")
            return redirect('app_catalogo_entorno:catalogo_entorno', entorno_id=entorno_id)
        else:
            messages.error(request, "Error al crear el producto. Revisa el formulario.")
    else:
        form = ProductoForm()
    
    context = {
        'form': form, 
        'entorno': entorno_actual,
        'page_title': "Crear Producto en Catálogo"
    }
    return render(request, 'app_catalogo_entorno/crear_producto_entorno.html', context)

@login_required
def editar_producto_entorno(request, pk): # pk del Producto
    producto_a_editar = get_object_or_404(Producto, pk=pk)
    if not producto_a_editar.entorno:
         messages.error(request, "Este producto no pertenece a ningún catálogo.")
         return redirect('app_home:dashboard') # O a donde sea apropiado

    if request.user != producto_a_editar.entorno.administrador:
        return HttpResponseForbidden("No tienes permiso para editar este producto del catálogo.")

    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES, instance=producto_a_editar)
        if form.is_valid():
            form.save()
            messages.success(request, f"Producto '{producto_a_editar.nombre}' actualizado.")
            return redirect('app_catalogo_entorno:catalogo_entorno', entorno_id=producto_a_editar.entorno.id)
        else:
            messages.error(request, "Error al actualizar el producto. Revisa el formulario.")
    else:
        form = ProductoForm(instance=producto_a_editar)
        
    context = {
        'form': form, 
        'entorno': producto_a_editar.entorno, 
        'producto': producto_a_editar,
        'page_title': f"Editar Producto: {producto_a_editar.nombre}"
    }
    return render(request, 'app_catalogo_entorno/editar_producto_entorno.html', context)

@login_required
def eliminar_producto_entorno(request, pk): # pk del Producto
    producto_a_eliminar = get_object_or_404(Producto, pk=pk)
    if not producto_a_eliminar.entorno:
        messages.error(request, "Este producto no pertenece a ningún catálogo para ser eliminado de él.")
        return redirect('app_home:dashboard') # O a donde sea apropiado

    entorno_id_original = producto_a_eliminar.entorno.id
    if request.user != producto_a_eliminar.entorno.administrador:
        return HttpResponseForbidden("No tienes permiso para eliminar este producto del catálogo.")

    if request.method == 'POST':
        nombre_producto = producto_a_eliminar.nombre
        # Opción 1: Quitar del catálogo (desvincular)
        # producto_a_eliminar.entorno = None
        # producto_a_eliminar.save()
        # messages.success(request, f"Producto '{nombre_producto}' quitado del catálogo.")
        
        # Opción 2: Eliminar el producto completamente (como estaba antes)
        producto_a_eliminar.delete()
        messages.success(request, f"Producto '{nombre_producto}' eliminado completamente.")
        
        return redirect('app_catalogo_entorno:catalogo_entorno', entorno_id=entorno_id_original)
    
    context = {
        'producto': producto_a_eliminar,
        'entorno': producto_a_eliminar.entorno,
        'page_title': f"Confirmar Eliminación de: {producto_a_eliminar.nombre}"
    }
    return render(request, 'app_catalogo_entorno/eliminar_producto_entorno.html', context)