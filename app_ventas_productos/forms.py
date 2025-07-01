from django import forms
from .models import VentaProducto
from app_cargar_productos.models import Producto

class RegistrarVentaForm(forms.ModelForm):
    class Meta:
        model = VentaProducto
        fields = ['producto', 'fecha_venta', 'cantidad_vendida', 'precio_unitario']
        widgets = {
            'fecha_venta': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        entorno_id = kwargs.pop('entorno_id', None)
        super().__init__(*args, **kwargs)
        if user and entorno_id:
            productos_entorno = Producto.objects.filter(entorno_id=entorno_id)
            productos_usuario = Producto.objects.filter(creado_por=user)
            self.fields['producto'].queryset = (productos_entorno | productos_usuario).distinct()
        elif user:
            self.fields['producto'].queryset = Producto.objects.filter(creado_por=user)

class CargarCSVVentasForm(forms.Form):
    archivo_csv = forms.FileField(label='Selecciona un archivo CSV')
