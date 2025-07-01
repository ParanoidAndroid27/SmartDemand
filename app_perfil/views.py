from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from login_smartdemand.models import UserProfile
from login_smartdemand.forms import EditarPerfilForm

@login_required
def perfil_view(request):
    perfil = UserProfile.objects.get(user=request.user)
    return render(request, 'app_perfil/perfil.html', {'perfil': perfil})

@login_required
def editar_perfil_view(request):
    perfil = UserProfile.objects.get(user=request.user)
    if request.method == 'POST':
        form = EditarPerfilForm(request.POST, request.FILES, instance=perfil, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('app_perfil:perfil')
    else:
        form = EditarPerfilForm(instance=perfil, user=request.user)
    return render(request, 'app_perfil/editar_perfil.html', {'form': form, 'perfil': perfil})
