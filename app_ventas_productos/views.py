from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import csv
from django.utils import timezone
from datetime import timedelta
from django import forms

from .forms import RegistrarVentaForm, CargarCSVVentasForm
from .models import VentaProducto
from app_cargar_productos.models import Producto

# ✅ Vista para registrar una venta manualmente
@login_required
def registrar_venta(request):
    entorno_id = request.session.get('entorno_activo_id')
    if request.method == 'POST':
        form = RegistrarVentaForm(request.POST, user=request.user, entorno_id=entorno_id)
        if form.is_valid():
            venta = form.save(commit=False)
            venta.creado_por = request.user
            venta.save()
            messages.success(request, 'Venta registrada correctamente.')
            return redirect('app_ventas_productos:registrar_venta')
        else:
            messages.error(request, 'Por favor, corrige los errores del formulario.')
    else:
        form = RegistrarVentaForm(user=request.user, entorno_id=entorno_id)
    return render(request, 'app_ventas_productos/registrar_venta.html', {'form': form})


# ✅ Vista para cargar ventas desde archivo CSV
@login_required
def cargar_ventas_csv(request):
    if request.method == 'POST':
        form = CargarCSVVentasForm(request.POST, request.FILES)
        if form.is_valid():
            archivo = request.FILES['archivo_csv']
            decoded = archivo.read().decode('utf-8').splitlines()
            reader = csv.DictReader(decoded)

            for row in reader:
                nombre_producto = row['producto'].strip()
                try:
                    # Cambiamos .get() por .filter().first() para evitar el error con nombres duplicados.
                    # Esto seleccionará el primer producto que coincida con el nombre.
                    producto = Producto.objects.filter(nombre=nombre_producto, creado_por=request.user).first()

                    if producto:
                        VentaProducto.objects.create(
                            producto=producto,
                            fecha_venta=row['fecha_venta'].strip(),
                            cantidad_vendida=int(row['cantidad_vendida']),
                            precio_unitario=float(row['precio_unitario']),
                            creado_por=request.user
                        )
                    else:
                        # Si el producto no se encuentra, lanzamos la excepción para que el manejador la capture.
                        raise Producto.DoesNotExist

                except Producto.DoesNotExist:
                    messages.warning(request, f"Producto '{nombre_producto}' no existe o no te pertenece. Venta omitida.")
                except Exception as e:
                    messages.error(request, f"Error con venta '{nombre_producto}': {str(e)}")

            messages.success(request, 'Archivo CSV de ventas procesado.')
            return redirect('app_ventas_productos:cargar_ventas_csv')
    else:
        form = CargarCSVVentasForm()

    return render(request, 'app_ventas_productos/cargar_ventas_csv.html', {'form': form})

class FiltroFechaForm(forms.Form):
    fecha_inicio = forms.DateField(required=False, label="Desde", widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    fecha_fin = forms.DateField(required=False, label="Hasta", widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))

@login_required
def listar_ventas(request):
    ventas = VentaProducto.objects.filter(creado_por=request.user).select_related('producto')
    hoy = timezone.now().date()
    hace_un_mes = hoy - timedelta(days=30)

    data_inicial = {
        'fecha_inicio': request.GET.get('fecha_inicio', ''),
        'fecha_fin': request.GET.get('fecha_fin', ''),
    }
    form = FiltroFechaForm(request.GET or None, initial=data_inicial)

    if form.is_valid() and (form.cleaned_data.get('fecha_inicio') or form.cleaned_data.get('fecha_fin')):
        fecha_inicio = form.cleaned_data.get('fecha_inicio')
        fecha_fin = form.cleaned_data.get('fecha_fin')
        if fecha_inicio:
            ventas = ventas.filter(fecha_venta__gte=fecha_inicio)
        if fecha_fin:
            ventas = ventas.filter(fecha_venta__lte=fecha_fin)
        ventas = ventas.order_by('-fecha_venta')
    else:
        # Solo las 30 más recientes por defecto
        ventas = ventas.order_by('-fecha_venta')[:30]

    return render(request, 'app_ventas_productos/listar_ventas.html', {
        'ventas': ventas,
        'form_filtro': form,
    })
