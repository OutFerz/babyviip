"""
Vistas de registro, login y logout.
Plantillas: templates/auth/registro.html, templates/auth/login.html
Formulario: erp.forms.RegistroUsuarioForm
"""

from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render

from .forms import BabyviipAuthenticationForm, RegistroUsuarioForm


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
