from django import forms
from app_cargar_productos.models import Producto, Categoria
from app_entornos_trabajo.models import EntornoTrabajo

class ProductoForm(forms.ModelForm):
    # CORRECCIÓN AQUÍ: El campo se llama 'entorno'
    entorno = forms.ModelChoiceField(
        queryset=EntornoTrabajo.objects.all(),
        required=False,
        label="Entorno de Trabajo"
    )

    class Meta:
        model = Producto
        # CORRECCIÓN AQUÍ: Agregamos 'destacado' a la lista de campos
        fields = ['nombre', 'descripcion', 'precio_unitario', 'stock', 'imagen', 'entorno', 'destacado']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(ProductoForm, self).__init__(*args, **kwargs)
        if user:
            entornos_admin = EntornoTrabajo.objects.filter(administrador=user)
            entornos_colab = user.entornos_donde_colabora.all()
            # CORRECCIÓN AQUÍ: Aplicamos el queryset al campo 'entorno'
            self.fields['entorno'].queryset = (entornos_admin | entornos_colab).distinct()