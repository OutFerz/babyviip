from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import Cliente, Usuario


class BabyviipAuthenticationForm(AuthenticationForm):
    """Login con clases Bootstrap en los inputs."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for _name, field in self.fields.items():
            field.widget.attrs.setdefault("class", "form-control")


class RegistroUsuarioForm(UserCreationForm):
    """Registro: crea Usuario + Cliente vinculado (datos de compra)."""

    email = forms.EmailField(required=True, label="Correo electrónico")
    nombre = forms.CharField(max_length=200, label="Nombre completo")
    rut = forms.CharField(max_length=12, label="RUT")
    contacto = forms.CharField(max_length=20, required=False, label="Teléfono (opcional)")

    class Meta:
        model = Usuario
        fields = ("username", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Nombre de usuario"
        for name, field in self.fields.items():
            field.widget.attrs.setdefault("class", "form-control")

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.email = self.cleaned_data["email"]
        usuario.es_cliente = True
        usuario.es_administrador_tienda = False
        if commit:
            usuario.save()
            Cliente.objects.create(
                usuario=usuario,
                nombre=self.cleaned_data["nombre"],
                rut=self.cleaned_data["rut"],
                email=self.cleaned_data["email"],
                contacto=self.cleaned_data.get("contacto") or None,
            )
        return usuario
