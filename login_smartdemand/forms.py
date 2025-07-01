from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile
from django.contrib.auth import authenticate


class RegistroForm(UserCreationForm):
    email = forms.EmailField(required=True)
    foto_perfil = forms.ImageField(required=False)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'foto_perfil']


class LoginConCorreoForm(forms.Form):
    email = forms.EmailField(label='Correo electrónico', max_length=254)
    password = forms.CharField(label='Contraseña', widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise forms.ValidationError('No existe un usuario con ese correo.')

        user = authenticate(username=user.username, password=password)
        if user is None:
            raise forms.ValidationError('La contraseña es incorrecta.')

        cleaned_data['user'] = user
        return cleaned_data


class EditarPerfilForm(forms.ModelForm):
    first_name = forms.CharField(label='Nombre', required=False)
    last_name = forms.CharField(label='Apellido', required=False)
    email = forms.EmailField(label='Correo electrónico', required=True)

    class Meta:
        model = UserProfile
        fields = ['foto_perfil']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email

    def save(self, commit=True):
        perfil = super().save(commit=False)
        user = self.instance.user
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            perfil.save()
        return perfil
