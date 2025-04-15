from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('registro/', views.register_view, name='registro'),  # ESTE NOMBRE
]
