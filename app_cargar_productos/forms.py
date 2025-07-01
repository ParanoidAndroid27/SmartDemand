from django import forms
from .models import Producto, Categoria

class ProductoForm(forms.ModelForm):
    categoria_nombre = forms.CharField(label="Categoría", max_length=255)

    class Meta:
        model = Producto
        # Se ha eliminado 'categoria_nombre' de esta lista porque no es un campo del modelo.
        fields = ['nombre', 'descripcion', 'stock', 'precio_unitario', 'imagen', 'destacado']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Solo se pre-carga la categoría al editar
        if self.instance and self.instance.pk and self.instance.categoria:
            self.fields['categoria_nombre'].initial = self.instance.categoria.nombre

    def save(self, commit=True, user=None):
        categoria_nombre = self.cleaned_data['categoria_nombre'].strip()
        categoria, created = Categoria.objects.get_or_create(nombre=categoria_nombre)

        producto = super().save(commit=False)
        producto.categoria = categoria

        if user and not producto.creado_por:
            producto.creado_por = user

        if commit:
            producto.save()
        return producto

# ✅ Formulario para subir CSV de productos
class CargarCSVForm(forms.Form):
    archivo_csv = forms.FileField(label='Selecciona un archivo CSV')
