from django.urls import path
from . import views

app_name = 'app_alertas_stock'

urlpatterns = [
    path('', views.ver_alertas, name='ver_alertas'),
    path('configurar/', views.configurar_alertas, name='configurar_alertas'),  # AÑADE ESTA LÍNEA
]