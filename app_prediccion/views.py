from collections import OrderedDict
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.db.models import Q
from app_ventas_productos.models import VentaProducto
from app_cargar_productos.models import Producto
from .services import (
    preparar_datos, tune_hyperparameters, entrenar_modelo,
    evaluar_modelo, predecir_proximos_dias,
    guardar_modelo, cargar_modelo
)
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os, uuid, numpy as np
from datetime import datetime, timedelta
import pandas as pd
from django.conf import settings

# PDF
from io import BytesIO
import os
from datetime import datetime, timedelta

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd

from django.conf import settings
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether
)

from app_cargar_productos.models import Producto
from app_ventas_productos.models import VentaProducto
from .services import preparar_datos, tune_hyperparameters, entrenar_modelo, predecir_proximos_dias
from .models import ExportacionReporte


@login_required
def dashboard_prediccion(request):
    entorno_activo_id = request.session.get('entorno_activo_id')

    # 1. Define el filtro para los productos que el usuario puede ver.
    filtro_productos = Q(creado_por=request.user)
    if entorno_activo_id:
        filtro_productos |= Q(entorno_id=entorno_activo_id)

    # 2. Obtiene la lista de productos disponibles para el selector.
    productos_disponibles = list(
        Producto.objects.filter(filtro_productos).values_list('id', 'nombre').distinct()
    )
    
    sel = None
    try:
        sel = int(request.GET.get('producto'))
    except (TypeError, ValueError):
        pass

    # 3. Si no se selecciona producto, muestra un mensaje.
    if not sel:
        return render(request, 'app_prediccion/dashboard.html', {
            'mensaje': 'Selecciona un producto de la lista para ver su análisis y predicción.',
            'productos_disponibles': productos_disponibles
        })

    # 4. Si se seleccionó, busca sus ventas.
    ventas = VentaProducto.objects.filter(producto=sel).order_by('fecha_venta')
    nombre = dict(productos_disponibles).get(sel, f'ID {sel}')

    # 5. Si no hay suficientes datos, muestra un mensaje.
    if ventas.count() < 30:
        return render(request, 'app_prediccion/dashboard.html', {
            'mensaje': 'No hay suficientes datos de venta para este producto para generar una predicción (se requieren al menos 30 registros).',
            'productos_disponibles': productos_disponibles,
            'producto_seleccionado': sel,
            'producto_nombre': nombre
        })

    # --- INICIO DE LA LÓGICA DE PREDICCIÓN ---
    df = preparar_datos(ventas)
    feats = [
        'dias','dia_semana','mes','ventas_lag1',
        'sem_sin','sem_cos','mes_sin','mes_cos',
        'prom_movil_7','precio_unitario'
    ]
    X, y = df[feats], df['cantidad_vendida']

    best = tune_hyperparameters(X, y)
    modelo = entrenar_modelo(X, y, modelo_base=best)
    guardar_modelo(modelo)

    rmse, r2 = evaluar_modelo(modelo, X, y)
    fechas_futuras, preds = predecir_proximos_dias(modelo, df)

    # Gráfico principal
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(df['fecha_venta'], y, linewidth=2, marker='o', markersize=4, label='Histórico')
    ax.plot(fechas_futuras, preds, linewidth=2, marker='X', markersize=6, linestyle='--', label='Predicción')
    for x_pt, y_pt in zip(fechas_futuras, preds):
        ax.annotate(f'{y_pt:.0f}', xy=(x_pt, y_pt),
                    xytext=(0, 6), textcoords='offset points',
                    ha='center', fontsize=9)
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
    ax.set_title(f'Predicción de ventas para: {nombre}', fontsize=14, fontweight='bold')
    ax.set_xlabel('Fecha', fontsize=12)
    ax.set_ylabel('Cantidad Vendida', fontsize=12)
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend(frameon=True, fontsize=11)
    plt.tight_layout()

    fn = f'pred_{uuid.uuid4().hex}.png'
    path = os.path.join('media', fn)
    plt.savefig(path); plt.close()
    grafico_url = '/' + path

    # Gráficos adicionales (semana y mes)
    hoy = datetime.now().date()
    lunes = hoy - timedelta(days=hoy.weekday())
    mask_sem = (df['fecha_venta'] >= pd.to_datetime(lunes)) & (df['fecha_venta'] <= pd.to_datetime(lunes + timedelta(days=6)))
    df_semana = df[mask_sem].copy()
    fechas_semana = [lunes + timedelta(days=i) for i in range(7)]
    ult_dia = df['dias'].max()
    df_futuros_sem = []
    for i, fecha in enumerate(fechas_semana, start=1):
        row = {
            'dias': ult_dia + i, 'dia_semana': fecha.weekday(), 'mes': fecha.month,
            'ventas_lag1': df['cantidad_vendida'].iloc[-1],
            'sem_sin': np.sin(2 * np.pi * fecha.weekday() / 7),
            'sem_cos': np.cos(2 * np.pi * fecha.weekday() / 7),
            'mes_sin': np.sin(2 * np.pi * ((fecha.month - 1) / 12)),
            'mes_cos': np.cos(2 * np.pi * ((fecha.month - 1) / 12)),
            'prom_movil_7': df['cantidad_vendida'].tail(7).mean(),
            'precio_unitario': df['precio_unitario'].iloc[-1]
        }
        df_futuros_sem.append(row)
    X_sem = pd.DataFrame(df_futuros_sem)
    preds_sem = modelo.predict(X_sem)

    fig2, ax2 = plt.subplots(figsize=(10,4))
    ax2.bar(df_semana['fecha_venta'], df_semana['cantidad_vendida'], color='#396ae8', label='Ventas reales')
    ax2.plot(fechas_semana, preds_sem, marker='o', linestyle='--', color='#fbbf24', label='Predicción')
    for x_pt, y_pt in zip(fechas_semana, preds_sem):
        ax2.annotate(f'{y_pt:.0f}', xy=(x_pt, y_pt), xytext=(0, 7), textcoords='offset points', ha='center', fontsize=9, color='#2346a7')
    ax2.set_title('Semana actual: Real vs Predicción'); ax2.set_xlabel('Fecha'); ax2.set_ylabel('Cantidad')
    ax2.legend(); ax2.grid(True, linestyle='--', alpha=0.3); plt.tight_layout()
    fn2 = f'sem_{uuid.uuid4().hex}.png'
    path2 = os.path.join('media', fn2)
    plt.savefig(path2); plt.close()
    grafico_sem_actual = '/' + path2

    primer_dia_mes = hoy.replace(day=1)
    mask_mes = (df['fecha_venta'] >= pd.to_datetime(primer_dia_mes)) & (df['fecha_venta'] <= pd.to_datetime(hoy))
    df_mes = df[mask_mes].copy()
    fig3, ax3 = plt.subplots(figsize=(10,4))
    ax3.bar(df_mes['fecha_venta'], df_mes['cantidad_vendida'], color='#2346a7', alpha=0.87)
    ax3.set_title('Ventas diarias del mes actual'); ax3.set_xlabel('Fecha'); ax3.set_ylabel('Cantidad vendida')
    ax3.xaxis.set_major_formatter(mdates.DateFormatter('%d-%b')); plt.setp(ax3.get_xticklabels(), rotation=45, ha='right')
    ax3.grid(True, linestyle='--', alpha=0.4); plt.tight_layout()
    fn3 = f'mes_{uuid.uuid4().hex}.png'
    path3 = os.path.join('media', fn3)
    plt.savefig(path3)
    plt.close()
    grafico_mes_actual = '/' + path3

    # Stock actual y alerta de stock bajo
    try:
        producto_obj = Producto.objects.get(id=sel)
        stock_actual = producto_obj.stock
    except Producto.DoesNotExist:
        stock_actual = None

    stock_bajo_prediccion = None
    stock_bajo = False
    if stock_actual is not None:
        for f, p in zip(fechas_futuras, preds):
            if stock_actual < p:
                stock_bajo_prediccion = (f, p)
                stock_bajo = True
                break

    riesgo = np.mean(preds) < np.percentile(y, 25)
    return render(request, 'app_prediccion/dashboard.html', {
        'grafico_url': grafico_url, 'grafico_sem_actual': grafico_sem_actual, 'grafico_mes_actual': grafico_mes_actual,
        'rmse': round(rmse, 2), 'r2': round(r2, 2), 'riesgo': riesgo,
        'predicciones_tabla': zip(fechas_futuras, preds),
        'productos_disponibles': productos_disponibles, 'producto_seleccionado': sel, 'producto_nombre': nombre,
        'stock_actual': stock_actual, 'stock_bajo': stock_bajo, 'stock_bajo_prediccion': stock_bajo_prediccion
    })


@login_required
def exportar_predicciones_pdf(request):
    """
    Genera un PDF moderno con:
     • Encabezado de color + logo.
     • Tres gráficos en memoria.
     • Tabla estilizada con filas alternadas.
     • Pie de página con copyright.
    """
    # 1. Filtrar permisos idénticos a dashboard
    entorno_activo_id = request.session.get('entorno_activo_id')
    filtro = Q(creado_por=request.user)
    if entorno_activo_id:
        filtro |= Q(entorno_id=entorno_activo_id)

    try:
        sel = int(request.GET.get('producto'))
    except (TypeError, ValueError):
        return HttpResponse("Producto inválido.", status=400)

    producto = get_object_or_404(Producto, id=sel)
    ventas = VentaProducto.objects.filter(producto=producto).order_by('fecha_venta')
    if ventas.count() < 30:
        return HttpResponse("Datos insuficientes para exportar.", status=400)

    nombre = producto.nombre
    # 2. Preparar datos y modelo
    df = preparar_datos(ventas)
    feats = ['dias','dia_semana','mes','ventas_lag1','sem_sin','sem_cos','mes_sin','mes_cos','prom_movil_7','precio_unitario']
    X, y = df[feats], df['cantidad_vendida']
    best = tune_hyperparameters(X, y)
    modelo = entrenar_modelo(X, y, modelo_base=best)
    from .services import evaluar_modelo
    rmse, r2 = evaluar_modelo(modelo, X, y)
    fechas_futuras, preds = predecir_proximos_dias(modelo, df)

    # Gráficos en memoria
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates

    # Gráfico 1: Histórico + Predicción
    fig, ax = plt.subplots(figsize=(8, 4), dpi=120)
    ax.plot(df['fecha_venta'], y, color="#2346a7", linewidth=2, marker='o', label='Histórico')
    ax.plot(fechas_futuras, preds, color="#fbbf24", linewidth=2, marker='X', linestyle='--', label='Predicción')
    ax.set_title('Histórico y Predicción de Ventas', fontsize=12, color="#2346a7")
    ax.set_xlabel('Fecha'); ax.set_ylabel('Cantidad')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
    ax.grid(True, linestyle='--', alpha=0.3)
    ax.legend()
    plt.tight_layout()
    bufimg1 = BytesIO()
    plt.savefig(bufimg1, format='PNG', bbox_inches='tight')
    plt.close(fig)
    bufimg1.seek(0)

    # Gráfico 2: Semana Actual
    hoy = df['fecha_venta'].max().date()
    lunes = hoy - timedelta(days=hoy.weekday())
    mask_sem = (df['fecha_venta'] >= pd.to_datetime(lunes)) & (df['fecha_venta'] <= pd.to_datetime(lunes + timedelta(days=6)))
    df_semana = df[mask_sem]
    fechas_semana = [lunes + timedelta(days=i) for i in range(7)]
    ult_dia = df['dias'].max()
    df_futuros_sem = []
    for i, fecha in enumerate(fechas_semana, start=1):
        df_futuros_sem.append({
            'dias': ult_dia + i,
            'dia_semana': fecha.weekday(),
            'mes': fecha.month,
            'ventas_lag1': df['cantidad_vendida'].iloc[-1],
            'sem_sin': np.sin(2*np.pi*fecha.weekday()/7),
            'sem_cos': np.cos(2*np.pi*fecha.weekday()/7),
            'mes_sin': np.sin(2*np.pi*((fecha.month-1)/12)),
            'mes_cos': np.cos(2*np.pi*((fecha.month-1)/12)),
            'prom_movil_7': df['cantidad_vendida'].tail(7).mean(),
            'precio_unitario': df['precio_unitario'].iloc[-1]
        })
    X2 = pd.DataFrame(df_futuros_sem)
    preds2 = modelo.predict(X2)
    fig2, ax2 = plt.subplots(figsize=(8, 4), dpi=120)
    ax2.bar(df_semana['fecha_venta'], df_semana['cantidad_vendida'], color='#396ae8', label='Ventas reales')
    ax2.plot(fechas_semana, preds2, marker='o', linestyle='--', color='#fbbf24', label='Predicción')
    ax2.set_title('Semana Actual: Real vs Predicción', fontsize=12, color="#2346a7")
    ax2.set_xlabel('Fecha'); ax2.set_ylabel('Cantidad')
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%d-%b'))
    plt.setp(ax2.get_xticklabels(), rotation=45, ha='right')
    ax2.legend()
    ax2.grid(True, linestyle='--', alpha=0.2)
    plt.tight_layout()
    bufimg2 = BytesIO()
    plt.savefig(bufimg2, format='PNG', bbox_inches='tight')
    plt.close(fig2)
    bufimg2.seek(0)

    # Gráfico 3: Mes Actual
    primer_dia_mes = hoy.replace(day=1)
    mask_mes = (df['fecha_venta'] >= pd.to_datetime(primer_dia_mes)) & (df['fecha_venta'] <= pd.to_datetime(hoy))
    df_mes = df[mask_mes]
    fig3, ax3 = plt.subplots(figsize=(8, 4), dpi=120)
    ax3.bar(df_mes['fecha_venta'], df_mes['cantidad_vendida'], color='#2346a7', alpha=0.87)
    ax3.set_title('Ventas Diarias del Mes Actual', fontsize=12, color="#2346a7")
    ax3.set_xlabel('Fecha'); ax3.set_ylabel('Cantidad vendida')
    ax3.xaxis.set_major_formatter(mdates.DateFormatter('%d-%b'))
    plt.setp(ax3.get_xticklabels(), rotation=45, ha='right')
    ax3.grid(True, linestyle='--', alpha=0.2)
    plt.tight_layout()
    bufimg3 = BytesIO()
    plt.savefig(bufimg3, format='PNG', bbox_inches='tight')
    plt.close(fig3)
    bufimg3.seek(0)

    # PDF armado
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    header_style = ParagraphStyle('Header', parent=styles['Heading1'], alignment=1, fontName='Helvetica-Bold', fontSize=18, textColor=colors.HexColor('#2346a7'), spaceAfter=12)
    kpi_style = ParagraphStyle('KPIs', fontSize=12, textColor=colors.HexColor('#2346a7'), backColor=colors.whitesmoke, spaceAfter=10, spaceBefore=10, alignment=1, leading=16)
    normal = styles['BodyText']
    normal.fontSize = 11

    # KPIs y alerta
    try:
        stock_actual = producto.stock
    except Exception:
        stock_actual = "N/A"
    alerta = ""
    if stock_actual != "N/A" and any(stock_actual < p for p in preds):
        alerta = "<b style='color:#e3342f;'>⚠️ Alerta:</b> El stock actual es menor que la demanda predicha en los próximos días."

    # Portada y KPIs
    elements = []
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'logo_fondo_blanco.png')
    if os.path.exists(logo_path):
        elements.append(Image(logo_path, width=3*cm, height=3*cm, hAlign='CENTER'))
    elements.append(Spacer(1, 0.2*cm))
    elements.append(Paragraph("Reporte de Predicción de Ventas", header_style))
    elements.append(Paragraph(f"<b>Producto:</b> {nombre}", normal))
    elements.append(Paragraph(f"<b>Generado:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}", normal))
    elements.append(Spacer(1, 0.3*cm))
    kpi_text = (
        f"<b>RMSE:</b> {round(rmse,2)} &nbsp;&nbsp; "
        f"<b>Precisión (R²):</b> {round(r2,2)} &nbsp;&nbsp; "
        f"<b>Stock actual:</b> {stock_actual if stock_actual is not None else 'N/A'} &nbsp;&nbsp; "
        f"<b>Ventas totales:</b> {int(y.sum())}"
    )
    elements.append(Paragraph(kpi_text, kpi_style))
    if alerta:
        elements.append(Paragraph(alerta, ParagraphStyle('Alerta', fontSize=11, textColor=colors.HexColor('#e3342f'), alignment=1, spaceAfter=10)))
    elements.append(PageBreak())

    # Gráficos (cada uno en su bloque KeepTogether)
    for title, buf in [
        ("Histórico y Predicción de Ventas", bufimg1),
        ("Semana Actual: Real vs Predicción", bufimg2),
        ("Ventas Diarias del Mes Actual", bufimg3)
    ]:
        block = [
            Paragraph(f"<b>{title}</b>", header_style),
            Spacer(1, 0.2*cm),
            Image(buf, width=16*cm, height=6*cm, hAlign='CENTER'),
            Spacer(1, 0.5*cm)
        ]
        elements.append(KeepTogether(block))
        elements.append(PageBreak())

    # Tabla de predicción (en su propia página)
    tabla_data = [["Fecha", "Predicción"]]
    for f, p in zip(fechas_futuras, preds):
        tabla_data.append([f.strftime("%d/%m/%Y"), f"{p:.2f}"])
    tabla = Table(tabla_data, colWidths=[6*cm, 6*cm])
    tabla.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#396ae8')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 12),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('BOX', (0,0), (-1,-1), 0.8, colors.grey),
    ]))
    for i in range(1, len(tabla_data)):
        color = colors.whitesmoke if i % 2 == 0 else colors.lightgrey
        tabla.setStyle(TableStyle([('BACKGROUND', (0,i), (-1,i), color)]))
    elements.append(KeepTogether([
        Paragraph("<b>Predicción para los próximos 7 días:</b>", normal),
        Spacer(1, 0.2*cm),
        tabla
    ]))
    elements.append(PageBreak())

    # Footer
    footer = Paragraph(
        "© 2025 SmartDemand – Reporte generado automáticamente",
        ParagraphStyle('Footer', alignment=1, fontSize=9, textColor=colors.HexColor('#2346a7'))
    )
    elements.append(footer)

    doc.build(elements)
    pdf_bytes = buffer.getvalue()  # <-- OBTÉN EL CONTENIDO ANTES DE CERRAR EL BUFFER
    buffer.seek(0)
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Prediccion_{nombre}.pdf"'
    from django.core.files.base import ContentFile
    ExportacionReporte.objects.create(
        usuario=request.user,
        archivo=ContentFile(pdf_bytes, name=f'Prediccion_{nombre}.pdf')
    )
    return response

@login_required
def ultimas_exportaciones(request):
    exportaciones = ExportacionReporte.objects.filter(usuario=request.user).order_by('-fecha')[:10]
    return render(request, 'app_prediccion/ultimas_exportaciones.html', {'exportaciones': exportaciones})