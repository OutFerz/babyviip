from django import forms
from django.forms import inlineformset_factory

from .models import Categoria, Cliente, ConfiguracionSitio, Producto, Variante


class ProductoPanelForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = (
            "nombre",
            "material",
            "imagen_url",
            "imagen",
            "categoria",
            "publicado",
        )
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "material": forms.TextInput(attrs={"class": "form-control"}),
            "imagen_url": forms.URLInput(
                attrs={
                    "class": "form-control",
                    "id": "id_imagen_url",
                    "autocomplete": "off",
                }
            ),
            "imagen": forms.ClearableFileInput(
                attrs={"class": "form-control", "id": "id_imagen_archivo"}
            ),
            "categoria": forms.Select(attrs={"class": "form-select"}),
            "publicado": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
        labels = {
            "publicado": "Visible en catálogo público",
            "imagen_url": "URL de imagen (opcional)",
            "imagen": "Subir imagen (opcional)",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["publicado"].help_text = (
            "Si desmarcas, el producto queda oculto en la vitrina (no se borra)."
        )
        self.fields["imagen_url"].help_text = (
            "Enlace externo a la foto. Si también subes un archivo, se mostrará el archivo."
        )
        self.fields["imagen"].help_text = (
            "Archivo local; tiene prioridad sobre la URL en el catálogo."
        )


class CategoriaPanelForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ("nombre", "descripcion")
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "descripcion": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
        }


class ConfiguracionSitioForm(forms.ModelForm):
    class Meta:
        model = ConfiguracionSitio
        fields = (
            "nombre_tienda",
            "texto_bienvenida",
            "instagram_usuario",
            "instagram_url",
            "facebook_nombre",
            "facebook_url",
            "telefono",
            "correo",
            "direccion",
            "mapa_url",
            "whatsapp_url",
        )
        widgets = {
            "nombre_tienda": forms.TextInput(attrs={"class": "form-control"}),
            "texto_bienvenida": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
            "instagram_usuario": forms.TextInput(attrs={"class": "form-control"}),
            "instagram_url": forms.URLInput(attrs={"class": "form-control"}),
            "facebook_nombre": forms.TextInput(attrs={"class": "form-control"}),
            "facebook_url": forms.URLInput(attrs={"class": "form-control"}),
            "telefono": forms.TextInput(attrs={"class": "form-control"}),
            "correo": forms.EmailInput(attrs={"class": "form-control"}),
            "direccion": forms.TextInput(attrs={"class": "form-control"}),
            "mapa_url": forms.URLInput(attrs={"class": "form-control"}),
            "whatsapp_url": forms.URLInput(attrs={"class": "form-control"}),
        }
        labels = {
            "texto_bienvenida": "Texto de bienvenida (Inicio)",
            "instagram_usuario": "Instagram (usuario)",
            "instagram_url": "Instagram (URL)",
            "facebook_nombre": "Facebook (texto)",
            "facebook_url": "Facebook (URL)",
            "telefono": "Teléfono",
            "correo": "Correo",
            "direccion": "Dirección del local",
            "mapa_url": "Mapa (URL)",
            "whatsapp_url": "WhatsApp (URL)",
        }


class SimuladorCompraForm(forms.Form):
    cliente = forms.ModelChoiceField(
        queryset=Cliente.objects.order_by("nombre"),
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
        help_text="Opcional. Si no eliges, la venta queda sin cliente asociado.",
    )
    modo = forms.ChoiceField(
        choices=[
            ("sin_impacto", "Sin impacto (no crea venta, no descuenta stock)"),
            ("temporal", "Temporal (crea venta simulada + descuenta stock; reversible)"),
            ("permanente", "Permanente (crea venta real + descuenta stock)"),
        ],
        initial="sin_impacto",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    estado = forms.ChoiceField(
        choices=[
            ("carrito", "Por comprar"),
            ("pendiente_pago", "Pendiente de pago"),
            ("pagado", "Comprado"),
            ("cancelado", "Pago cancelado"),
        ],
        initial="carrito",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    line_count = forms.IntegerField(
        required=False,
        initial=3,
        widget=forms.HiddenInput(),
    )
    confirmar_permanente = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        label="Confirmo que este modo crea una venta REAL y afecta stock/reportes",
    )

    def clean(self):
        cleaned = super().clean()
        modo = (cleaned.get("modo") or "").strip()
        if modo == "permanente" and not cleaned.get("confirmar_permanente"):
            self.add_error(
                "confirmar_permanente",
                "Debes confirmar para ejecutar una venta real (modo permanente).",
            )
        # line_count mínimo 1, máximo 30 (protección)
        try:
            n = int(cleaned.get("line_count") or 3)
        except (TypeError, ValueError):
            n = 3
        cleaned["line_count"] = max(1, min(30, n))
        return cleaned


class SimuladorLineaForm(forms.Form):
    variante = forms.ModelChoiceField(
        queryset=Variante.objects.select_related("producto").order_by(
            "producto__nombre", "talla_etiqueta", "color"
        ),
        required=False,
        widget=forms.Select(attrs={"class": "form-select form-select-sm"}),
    )
    cantidad = forms.IntegerField(
        min_value=1,
        initial=1,
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control form-control-sm"}),
    )

    def clean(self):
        cleaned = super().clean()
        v = cleaned.get("variante")
        qty = cleaned.get("cantidad")
        # Permitir filas vacías (para que el simulador no "se quede" sin feedback)
        if not v and (qty is None or qty == ""):
            return cleaned
        if v and not qty:
            self.add_error("cantidad", "Indica una cantidad válida.")
        if qty and not v:
            self.add_error("variante", "Selecciona una variante.")
        return cleaned


VarianteFormSet = inlineformset_factory(
    Producto,
    Variante,
    fields=(
        "sku_unico",
        "talla_etiqueta",
        "meses_min",
        "meses_max",
        "color",
        "precio_unitario",
        "stock",
        "visible",
        "fecha_reposicion",
    ),
    extra=1,
    can_delete=True,
    min_num=0,
    widgets={
        "sku_unico": forms.TextInput(attrs={"class": "form-control form-control-sm"}),
        "talla_etiqueta": forms.TextInput(attrs={"class": "form-control form-control-sm"}),
        "meses_min": forms.NumberInput(attrs={"class": "form-control form-control-sm"}),
        "meses_max": forms.NumberInput(attrs={"class": "form-control form-control-sm"}),
        "color": forms.TextInput(attrs={"class": "form-control form-control-sm"}),
        "precio_unitario": forms.NumberInput(
            attrs={"class": "form-control form-control-sm", "step": "0.01"}
        ),
        "stock": forms.NumberInput(attrs={"class": "form-control form-control-sm"}),
        "visible": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        "fecha_reposicion": forms.DateInput(
            attrs={"class": "form-control form-control-sm", "type": "date"}
        ),
    },
)
