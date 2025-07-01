from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from .models import EntornoTrabajo
from .forms import AgregarColaboradorForm, CrearEntornoForm

@login_required
def gestionar_entorno_trabajo(request):
    """
    Vista para crear/editar el entorno donde eres ADMIN.
    NO pisa la sesión en GET, sólo guarda al crear o actualizar.
    """
    form_creacion = None
    form_agregar = None
    colaboradores = []
    entorno_admin = None

    try:
        entorno_admin = EntornoTrabajo.objects.get(administrador=request.user)
        colaboradores = entorno_admin.colaboradores.all()
        form_agregar = AgregarColaboradorForm()

        if request.method == 'POST':
            # Actualizar nombre
            if 'actualizar_nombre_entorno' in request.POST:
                nuevo = request.POST.get('nombre_entorno_actualizar','').strip()
                entorno_admin.nombre = nuevo or None
                entorno_admin.save()
                messages.success(request, "Nombre del entorno actualizado.")
                return redirect('app_entornos_trabajo:gestionar_entorno')

            # Eliminar colaborador
            if 'eliminar_colaborador_id' in request.POST:
                cid = request.POST.get('eliminar_colaborador_id')
                try:
                    col = User.objects.get(id=cid)
                    if col in entorno_admin.colaboradores.all():
                        entorno_admin.colaboradores.remove(col)
                        messages.success(request, f"Colaborador '{col.username}' eliminado.")
                    else:
                        messages.warning(request, "Usuario no era colaborador.")
                except User.DoesNotExist:
                    messages.error(request, "Usuario no encontrado.")
                return redirect('app_entornos_trabajo:gestionar_entorno')

    except EntornoTrabajo.DoesNotExist:
        # Si no eres admin de ningún entorno, ofrezco crear
        if request.method == 'POST':
            form_creacion = CrearEntornoForm(request.POST)
            if form_creacion.is_valid():
                nuevo = form_creacion.save(commit=False)
                nuevo.administrador = request.user
                nuevo.save()
                # Fijo la sesión al nuevo entorno
                request.session['entorno_activo_id'] = nuevo.id
                messages.success(request, f"Entorno '{nuevo.nombre or nuevo.administrador.username}' creado y activado.")
                return redirect('app_entornos_trabajo:gestionar_entorno')
            else:
                messages.error(request, "Error al crear el entorno. Revisa los datos.")
        else:
            form_creacion = CrearEntornoForm()

    return render(request, 'app_entornos_trabajo/gestionar_entorno.html', {
        'entorno_trabajo': entorno_admin,
        'colaboradores_entorno': colaboradores,
        'form_agregar_colaborador': form_agregar,
        'form_creacion': form_creacion,
        'page_title': "Gestionar mi Entorno de Trabajo"
    })


@login_required
def agregar_colaborador(request):
    """Añade un colaborador al entorno que administras."""
    try:
        entorno = EntornoTrabajo.objects.get(administrador=request.user)
    except EntornoTrabajo.DoesNotExist:
        messages.error(request, 'No eres administrador de ningún entorno.')
        return redirect('app_entornos_trabajo:gestionar_entorno')

    if request.method == 'POST':
        form = AgregarColaboradorForm(request.POST)
        if form.is_valid():
            dato = form.cleaned_data['usuario_o_email'].strip()
            # Busco por username o email
            try:
                user = User.objects.get(username=dato)
            except User.DoesNotExist:
                try:
                    user = User.objects.get(email=dato)
                except User.DoesNotExist:
                    user = None

            if not user:
                messages.error(request, 'Usuario no encontrado.')
            elif user == request.user:
                messages.error(request, 'No puedes agregarte a ti mismo.')
            elif user in entorno.colaboradores.all():
                messages.warning(request, f"'{user.username}' ya es colaborador.")
            else:
                entorno.colaboradores.add(user)
                messages.success(request, f"Se agregó a '{user.username}'.")
        else:
            messages.error(request, 'Error en el formulario de colaborador.')
    return redirect('app_entornos_trabajo:gestionar_entorno')


@login_required
def listar_y_seleccionar_entornos(request):
    """Muestra todos tus entornos (admin + colaborador) y permite activarlos."""
    # Admin
    try:
        env_admin = EntornoTrabajo.objects.get(administrador=request.user)
        admin_list = [env_admin]
    except EntornoTrabajo.DoesNotExist:
        admin_list = []

    # Colaborador
    col_list = list(request.user.entornos_donde_colabora.all())

    todos = list({*admin_list, *col_list})
    activo = request.session.get('entorno_activo_id')

    return render(request, 'app_entornos_trabajo/listar_y_seleccionar_entornos.html', {
        'entornos': todos,
        'entorno_activo_id': activo,
        'page_title': "Mis Entornos de Trabajo"
    })


@login_required
def activar_entorno_sesion(request, entorno_id):
    """Fija en sesión el entorno que el usuario seleccionó, si tiene permiso."""
    env = get_object_or_404(EntornoTrabajo, id=entorno_id)
    es_admin = (env.administrador == request.user)
    es_colab = request.user in env.colaboradores.all()

    if es_admin or es_colab:
        request.session['entorno_activo_id'] = env.id
        name = env.nombre or f"Entorno de {env.administrador.username}"
        messages.success(request, f"Entorno '{name}' activado.")
    else:
        messages.error(request, "No tienes permiso para activar este entorno.")

    return redirect('app_entornos_trabajo:listar_y_seleccionar_entornos')
