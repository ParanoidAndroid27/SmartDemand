# app_estadisticas/urls.py
from django.urls import path
from . import views

app_name = 'app_estadisticas'

urlpatterns = [
    path(
        'colaborador/<int:entorno_id>/<int:colaborador_id>/',
        views.estadisticas_colaborador,
        name='estadisticas_colaborador'
    ),

]
