from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.forms import modelformset_factory
from django.db.models import Q
from app_entornos_trabajo.models import EntornoTrabajo
from app_cargar_productos.models import Producto
from .models import AlertaStock

@login_required
def ver_alertas(request):
    productos_con_alerta = []
    entorno_actual = None
    
    # CORRECCIÓN AQUÍ: Usamos 'entorno_activo_id' en lugar de 'entorno_actual_id'
    entorno_activo_id = request.session.get('entorno_activo_id')

    if entorno_activo_id:
        try:
            entorno_actual = EntornoTrabajo.objects.get(id=entorno_activo_id)
            alertas_configuradas = AlertaStock.objects.filter(
                entorno_trabajo=entorno_actual, 
                activo=True
            ).select_related('producto')

            for alerta in alertas_configuradas:
                if alerta.producto.stock <= alerta.umbral_minimo:
                    productos_con_alerta.append(alerta)
        except EntornoTrabajo.DoesNotExist:
            pass

    context = {
        'alertas': productos_con_alerta,
        'entorno_actual': entorno_actual
    }
    return render(request, 'app_alertas_stock/ver_alertas.html', context)

@login_required
def configurar_alertas(request):
    # CORRECCIÓN AQUÍ: Usamos 'entorno_activo_id' en lugar de 'entorno_actual_id'
    entorno_activo_id = request.session.get('entorno_activo_id')
    if not entorno_activo_id:
        messages.warning(request, 'Para configurar alertas, primero debes seleccionar un entorno de trabajo.')
        return redirect('app_entornos_trabajo:listar_y_seleccionar_entornos')

    try:
        entorno_actual = EntornoTrabajo.objects.get(id=entorno_activo_id)
    except EntornoTrabajo.DoesNotExist:
        messages.error(request, 'El entorno de trabajo activo no es válido.')
        return redirect('app_entornos_trabajo:listar_y_seleccionar_entornos')

    # AQUÍ ESTÁ LA NUEVA LÓGICA:
    # Buscamos productos que estén en el entorno actual O que hayan sido creados por el usuario.
    productos_a_configurar = Producto.objects.filter(
        Q(entorno=entorno_actual) | Q(creado_por=request.user)
    ).distinct()

    if not productos_a_configurar.exists():
        messages.info(
            request, 
            f"No se encontraron productos en el entorno '{entorno_actual.nombre}' ni productos creados por ti."
        )
        return redirect('app_alertas_stock:ver_alertas')

    # Aseguramos que cada producto visible tenga una configuración de alerta PARA ESTE ENTORNO.
    # Esto "importa" tus productos personales a la configuración del entorno activo.
    for producto in productos_a_configurar:
        AlertaStock.objects.get_or_create(
            producto=producto,
            entorno_trabajo=entorno_actual
        )

    # El formset ahora trabajará con todas las alertas del entorno, que ya incluyen tus productos.
    AlertaStockFormSet = modelformset_factory(
        AlertaStock,
        fields=('umbral_minimo', 'activo'),
        extra=0
    )

    queryset = AlertaStock.objects.filter(entorno_trabajo=entorno_actual).select_related('producto')

    if request.method == 'POST':
        formset = AlertaStockFormSet(request.POST, queryset=queryset)
        if formset.is_valid():
            formset.save()
            messages.success(request, '¡La configuración de alertas se ha guardado correctamente!')
            return redirect('app_alertas_stock:ver_alertas')
        else:
            messages.error(request, 'Por favor, corrige los errores en el formulario.')
    else:
        formset = AlertaStockFormSet(queryset=queryset)

    context = {
        'formset': formset,
        'entorno_actual': entorno_actual,
    }
    return render(request, 'app_alertas_stock/configurar_alertas.html', context)
