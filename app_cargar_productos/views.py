# app_cargar_productos/views.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import ProductoForm, CargarCSVForm
from .models import Producto, Categoria
import csv

# Agregar producto manualmente
@login_required
def agregar_producto(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save(user=request.user)
            messages.success(request, 'Producto agregado correctamente.')
            return redirect('app_cargar_productos:agregar_producto')
        else:
            messages.error(request, 'Por favor, corrige los errores en el formulario.')
    else:
        form = ProductoForm()

    return render(request, 'app_cargar_productos/agregar_producto.html', {'form': form})


# Cargar productos desde CSV
@login_required
def cargar_csv(request):
    if request.method == 'POST':
        form = CargarCSVForm(request.POST, request.FILES)
        if form.is_valid():
            archivo = request.FILES['archivo_csv']
            decoded = archivo.read().decode('utf-8').splitlines()
            reader = csv.DictReader(decoded)

            for row in reader:
                try:
                    categoria_nombre = row['categoria'].strip()
                    categoria, _ = Categoria.objects.get_or_create(nombre=categoria_nombre)
                    Producto.objects.create(
                        nombre=row['nombre'].strip(),
                        descripcion=row['descripcion'].strip(),
                        categoria=categoria,
                        stock=int(row['stock']),
                        precio_unitario=float(row['precio_unitario']),
                        creado_por=request.user
                    )
                except Exception as e:
                    messages.error(request, f"Error con producto '{row.get('nombre', 'Desconocido')}': {str(e)}")

            messages.success(request, 'Archivo CSV procesado.')
            return redirect('app_cargar_productos:cargar_csv')
    else:
        form = CargarCSVForm()

    return render(request, 'app_cargar_productos/cargar_csv.html', {'form': form})
