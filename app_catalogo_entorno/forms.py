# filepath: c:\SmartDemand\app_catalogo_entorno\forms.py
from django import forms
from app_cargar_productos.models import Producto

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['nombre','descripcion','precio_unitario','stock','imagen']