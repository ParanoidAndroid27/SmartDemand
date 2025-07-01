# app_prediccion/urls.py
from django.urls import path
from . import views

app_name = 'app_prediccion'

urlpatterns = [
    path('dashboard/', views.dashboard_prediccion, name='dashboard_prediccion'),
    path('exportar_pdf/', views.exportar_predicciones_pdf, name='exportar_pdf'),  # <-- ESTA LÍNEA!
    path('mis-exportaciones/', views.ultimas_exportaciones, name='ultimas_exportaciones'),
]
