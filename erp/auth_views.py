"""
Vistas de registro, login, logout y edición de perfil.
Plantillas: templates/auth/registro.html, templates/auth/login.html, templates/auth/perfil.html
"""

from django.contrib import messages
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render

from .auditoria import log_event
from .forms import BabyviipAuthenticationForm, PerfilForm, RegistroUsuarioForm
from .models import Cliente


def _cliente_de_usuario(user):
    try:
        return user.perfil_cliente
    except Cliente.DoesNotExist:
        return None


def registro(request):
    if request.user.is_authenticated:
        return redirect("home")
    if request.method == "POST":
        form = RegistroUsuarioForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            login(request, usuario)
            return redirect("home")
    else:
        form = RegistroUsuarioForm()
    return render(request, "auth/registro.html", {"form": form})


class BabyviipLoginView(LoginView):
    template_name = "auth/login.html"
    authentication_form = BabyviipAuthenticationForm
    redirect_authenticated_user = True


class BabyviipLogoutView(LogoutView):
    next_page = "/"


@login_required(login_url="/accounts/login/")
def editar_perfil(request):
    cliente = _cliente_de_usuario(request.user)
    if request.method == "POST":
        form = PerfilForm(
            request.POST,
            user=request.user,
            cliente=cliente,
        )
        if form.is_valid():
            password_changed = bool(form.cleaned_data.get("nueva_password"))
            user = form.save()
            if password_changed:
                update_session_auth_hash(request, user)
            log_event(
                request=request,
                usuario=user,
                accion="editar",
                modulo="cuenta",
                entidad="Usuario",
                entidad_id=str(user.pk),
                descripcion="Actualizar perfil de usuario y datos de cliente",
            )
            messages.success(request, "Tu perfil se actualizó correctamente.")
            return redirect("perfil_editar")
    else:
        form = PerfilForm(user=request.user, cliente=cliente)

    return render(
        request,
        "auth/perfil.html",
        {"form": form, "cliente": cliente},
    )
