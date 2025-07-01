"""
URL configuration for SmartDemand project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('web_smartdemand.urls')),                # Página principal
    path('auth/', include('login_smartdemand.urls')),         # Login, registro, perfil
    path('productos/', include('app_cargar_productos.urls')), #cargar productos
    path('ventas/', include('app_ventas_productos.urls')), #gestion de ventas 
    path('mis-productos/', include('app_gestion_productos.urls')),  #gestion de productos
    path('prediccion/', include('app_prediccion.urls')), #predicciones
    path('entornos/', include('app_entornos_trabajo.urls', namespace='app_entornos_trabajo')), # <--- AÑADE ESTA LÍNEA
    path( "estadisticas/",include(("app_estadisticas.urls", "app_estadisticas"),namespace="app_estadisticas"),),
    path('entornos/catalogo/', include('app_catalogo_entorno.urls')),
    path('alertas/', include('app_alertas_stock.urls')), # Ruta para la nueva app de alertas
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('perfil/', include('app_perfil.urls')),
]

# Media para fotos de perfil
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
