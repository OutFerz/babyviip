from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError

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


class PerfilForm(forms.Form):
    """Editar cuenta de acceso y ficha Cliente vinculada (si existe o se completa)."""

    username = forms.CharField(max_length=150, label="Nombre de usuario")
    email = forms.EmailField(label="Correo electrónico")
    nombre = forms.CharField(max_length=200, required=False, label="Nombre completo")
    rut = forms.CharField(max_length=12, required=False, label="RUT")
    contacto = forms.CharField(max_length=20, required=False, label="Teléfono (opcional)")
    nueva_password = forms.CharField(
        required=False,
        label="Nueva contraseña",
        widget=forms.PasswordInput(render_value=False),
        help_text="Déjala vacía si no quieres cambiarla.",
    )
    confirmar_password = forms.CharField(
        required=False,
        label="Confirmar nueva contraseña",
        widget=forms.PasswordInput(render_value=False),
    )

    def __init__(self, *args, user=None, cliente=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.cliente = cliente
        if user:
            self.fields["username"].initial = user.username
            self.fields["email"].initial = user.email
        if cliente:
            self.fields["nombre"].initial = cliente.nombre
            self.fields["rut"].initial = cliente.rut
            self.fields["contacto"].initial = cliente.contacto or ""
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")

    def clean_username(self):
        username = (self.cleaned_data.get("username") or "").strip()
        if not username:
            raise ValidationError("El nombre de usuario es obligatorio.")
        if (
            self.user
            and Usuario.objects.filter(username=username)
            .exclude(pk=self.user.pk)
            .exists()
        ):
            raise ValidationError("Ese nombre de usuario ya está en uso.")
        return username

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip()
        if not email:
            raise ValidationError("El correo es obligatorio.")
        if (
            self.user
            and Usuario.objects.filter(email__iexact=email)
            .exclude(pk=self.user.pk)
            .exists()
        ):
            raise ValidationError("Ese correo ya está registrado en otra cuenta.")
        qs = Cliente.objects.filter(email__iexact=email)
        if self.cliente:
            qs = qs.exclude(pk=self.cliente.pk)
        if qs.exists():
            raise ValidationError(
                "Ese correo ya está asociado a otra ficha de cliente."
            )
        return email

    def clean_rut(self):
        rut = (self.cleaned_data.get("rut") or "").strip()
        if not rut:
            return rut
        qs = Cliente.objects.filter(rut=rut)
        if self.cliente:
            qs = qs.exclude(pk=self.cliente.pk)
        if qs.exists():
            raise ValidationError("Ese RUT ya está registrado en otra ficha de cliente.")
        return rut

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("nueva_password") or ""
        p2 = cleaned.get("confirmar_password") or ""
        if p1 or p2:
            if p1 != p2:
                self.add_error(
                    "confirmar_password",
                    "Las contraseñas no coinciden.",
                )
            elif len(p1) < 8:
                self.add_error(
                    "nueva_password",
                    "La contraseña debe tener al menos 8 caracteres.",
                )
        nombre = (cleaned.get("nombre") or "").strip()
        rut = (cleaned.get("rut") or "").strip()
        if not self.cliente and (nombre or rut) and not (nombre and rut):
            self.add_error(
                "nombre",
                "Para crear tu ficha de cliente, completa nombre y RUT.",
            )
        return cleaned

    def save(self):
        user = self.user
        user.username = self.cleaned_data["username"]
        user.email = self.cleaned_data["email"]
        password = self.cleaned_data.get("nueva_password") or ""
        if password:
            user.set_password(password)
        user.save()

        nombre = (self.cleaned_data.get("nombre") or "").strip()
        rut = (self.cleaned_data.get("rut") or "").strip()
        contacto = (self.cleaned_data.get("contacto") or "").strip() or None

        if self.cliente:
            if nombre:
                self.cliente.nombre = nombre
            if rut:
                self.cliente.rut = rut
            self.cliente.contacto = contacto
            self.cliente.email = user.email
            self.cliente.save()
        elif nombre and rut:
            Cliente.objects.create(
                usuario=user,
                nombre=nombre,
                rut=rut,
                email=user.email,
                contacto=contacto,
            )
        return user
