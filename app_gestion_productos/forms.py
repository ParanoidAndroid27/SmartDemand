from django import forms
from app_cargar_productos.models import Producto, Categoria
from app_entornos_trabajo.models import EntornoTrabajo

class ProductoForm(forms.ModelForm):
    # Añadimos el campo para editar la categoría por su nombre
    categoria_nombre = forms.CharField(
        label="Categoría", 
        max_length=255,
        help_text="Si la categoría no existe, se creará una nueva."
    )
    
    entorno = forms.ModelChoiceField(
        queryset=EntornoTrabajo.objects.all(),
        required=False,
        label="Entorno de Trabajo"
    )

    class Meta:
        model = Producto
        # Añadimos 'destacado' y quitamos 'entorno' que se define arriba
        fields = ['nombre', 'descripcion', 'precio_unitario', 'stock', 'imagen', 'destacado', 'entorno']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(ProductoForm, self).__init__(*args, **kwargs)
        
        # Lógica para pre-rellenar el nombre de la categoría al editar
        if self.instance and self.instance.pk and self.instance.categoria:
            self.fields['categoria_nombre'].initial = self.instance.categoria.nombre

        # Lógica para limitar los entornos a los que el usuario tiene acceso
        if user:
            entornos_admin = EntornoTrabajo.objects.filter(administrador=user)
            entornos_colab = user.entornos_donde_colabora.all()
            self.fields['entorno'].queryset = (entornos_admin | entornos_colab).distinct()

    def save(self, commit=True):
        # Obtenemos o creamos la categoría a partir del nombre
        categoria_nombre = self.cleaned_data.get('categoria_nombre', '').strip()
        if categoria_nombre:
            categoria, _ = Categoria.objects.get_or_create(nombre=categoria_nombre)
            self.instance.categoria = categoria
        
        return super().save(commit=commit)