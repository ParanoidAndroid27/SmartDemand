from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from app_entornos_trabajo.models import EntornoTrabajo
from app_ventas_productos.models import VentaProducto
from app_cargar_productos.models import Producto # Asumiendo que aquí está tu modelo Producto
from django.db.models import Sum, Count, F, ExpressionWrapper, DecimalField
from django.contrib import messages
import json
from django.db.models.functions import TruncMonth
from django.core.serializers.json import DjangoJSONEncoder

@login_required
def estadisticas_colaborador(request, entorno_id, colaborador_id):
    entorno = get_object_or_404(EntornoTrabajo, id=entorno_id)
    colaborador = get_object_or_404(User, id=colaborador_id)

    # Validar permisos
    if request.user != entorno.administrador:
        messages.error(request, "No tienes permiso para acceder a estas estadísticas.")
        return redirect('app_entornos_trabajo:listar_y_seleccionar_entornos')
    
    ventas_del_colaborador_en_entorno = VentaProducto.objects.filter(
        creado_por=colaborador,
        producto__entorno=entorno
    ).annotate(
        ingresos_por_venta=ExpressionWrapper(F('cantidad_vendida') * F('precio_unitario'), output_field=DecimalField())
    )

    total_cantidad_vendida = ventas_del_colaborador_en_entorno.aggregate(total=Sum('cantidad_vendida'))['total'] or 0
    total_ingresos = ventas_del_colaborador_en_entorno.aggregate(total=Sum('ingresos_por_venta'))['total'] or 0
    numero_de_ventas = ventas_del_colaborador_en_entorno.count()
    productos_creados = Producto.objects.filter(creado_por=colaborador, entorno=entorno).count()

    # Ventas por mes
    ventas_por_mes = (
        ventas_del_colaborador_en_entorno
        .annotate(mes=TruncMonth('fecha_venta'))
        .values('mes')
        .annotate(total=Sum('cantidad_vendida'))
        .order_by('mes')
    )
    labels_ventas_mes = [v['mes'].strftime('%b %Y') for v in ventas_por_mes]
    data_ventas_mes = [v['total'] for v in ventas_por_mes]

    # Productos más vendidos
    productos_vendidos = (
        ventas_del_colaborador_en_entorno
        .values('producto__nombre')
        .annotate(total=Sum('cantidad_vendida'))
        .order_by('-total')[:5]
    )
    labels_productos = [p['producto__nombre'] for p in productos_vendidos]
    data_productos = [p['total'] for p in productos_vendidos]

    context = {
        'entorno': entorno,
        'colaborador': colaborador,
        'ventas': ventas_del_colaborador_en_entorno,
        'total_cantidad_vendida': total_cantidad_vendida,
        'total_ingresos': total_ingresos,
        'num_ventas': numero_de_ventas,
        'productos_creados': productos_creados,
        'labels_ventas_mes': json.dumps(labels_ventas_mes, cls=DjangoJSONEncoder),
        'data_ventas_mes': json.dumps(data_ventas_mes, cls=DjangoJSONEncoder),
        'labels_productos': json.dumps(labels_productos, cls=DjangoJSONEncoder),
        'data_productos': json.dumps(data_productos, cls=DjangoJSONEncoder),
    }
    return render(request, 'app_estadisticas/estadisticas_colaborador.html', context)