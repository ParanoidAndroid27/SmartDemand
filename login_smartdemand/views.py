from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.db import DatabaseError, IntegrityError
from .forms import RegistroForm, LoginConCorreoForm, EditarPerfilForm
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .models import UserProfile

# REGISTRO
def register_view(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                user = form.save()
                foto = form.cleaned_data.get('foto_perfil')
                if foto:
                    user.userprofile.foto_perfil = foto
                    user.userprofile.save()
                messages.success(request, '¡Registro exitoso! Bienvenido a SmartDemand.')
                login(request, user)
                return redirect('/')
            except (IntegrityError, DatabaseError) as e:
                error_text = str(e).lower()
                if 'correo electrónico' in error_text or 'email' in error_text:
                    messages.error(request, 'Este correo electrónico ya está registrado.')
                elif 'uid' in error_text:
                    messages.error(request, 'Este identificador único ya está registrado.')
                else:
                    messages.error(request, 'Ocurrió un error al registrar el usuario.')
        else:
            messages.error(request, 'Datos inválidos. Revisa el formulario.')
    else:
        form = RegistroForm()
    return render(request, 'users/register_page.html', {'form': form})
# LOGIN
def login_view(request):
    if request.method == 'POST':
        form = LoginConCorreoForm(request.POST)
        if form.is_valid():
            try:
                user = form.cleaned_data['user']
                login(request, user)
                messages.success(request, f'¡Bienvenido {user.username}!')
                return redirect('/')
            except DatabaseError:
                messages.error(request, 'Error de base de datos al intentar iniciar sesión.')
        else:
            messages.error(request, 'Correo o contraseña inválidos.')
    else:
        form = LoginConCorreoForm()
    return render(request, 'users/login_page.html', {'form': form})

@login_required
def perfil_view(request):
    perfil = UserProfile.objects.get(user=request.user)
    return render(request, 'users/perfil.html', {'perfil': perfil})

@login_required
def editar_perfil_view(request):
    perfil = UserProfile.objects.get(user=request.user)
    if request.method == 'POST':
        form = EditarPerfilForm(request.POST, request.FILES, instance=perfil, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil actualizado correctamente.')
            return redirect('perfil')
    else:
        form = EditarPerfilForm(instance=perfil, user=request.user)
    return render(request, 'users/editar_perfil.html', {'form': form, 'perfil': perfil})
