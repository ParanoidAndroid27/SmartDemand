from django.urls import path
from . import views

app_name = 'web_smartdemand'

urlpatterns = [
    path('', views.principal_page, name='principal_page'),
]