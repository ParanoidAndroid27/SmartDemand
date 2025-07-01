from django.urls import path
from .views import register_view, login_view

urlpatterns = [
    path('registro/', register_view, name='registro'),
    path('login/', login_view, name='login'),
]
