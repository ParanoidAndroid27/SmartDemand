#### forms.py
# filepath: c:\SmartDemand\app_entornos_trabajo\forms.py
from django import forms
from .models import EntornoTrabajo

class AgregarColaboradorForm(forms.Form):
    usuario_o_email = forms.CharField(
        label="Nombre de usuario o email del colaborador",
        max_length=254,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: juanperez o juan@ejemplo.com'})
    )

class CrearEntornoForm(forms.ModelForm):
    class Meta:
        model = EntornoTrabajo
        fields = ['nombre']
        widgets = {
            'nombre': forms.TextInput(attrs={'placeholder': 'Ej: Mi Negocio Principal'}),
        }
        labels = {
            'nombre': 'Nombre para tu Nuevo Entorno (opcional)',
        }
        help_texts = {
            'nombre': 'Si lo dejas en blanco, se usará tu nombre de usuario.'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nombre'].required = False # El nombre del entorno es opcional