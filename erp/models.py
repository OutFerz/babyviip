from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.db import models


# --- AUTENTICACIÓN (separado de Cliente / facturación) ---


class Usuario(AbstractUser):
    """
    Quien inicia sesión. No confundir con Cliente (datos de compra / boleta).
    Roles: es_cliente (tienda), es_administrador_tienda (panel operativo).
    """

    es_cliente = models.BooleanField(default=True)
    es_administrador_tienda = models.BooleanField(default=False)
    es_empleado = models.BooleanField(
        default=False,
        help_text="Rol interno con acceso limitado (ej: auditoría propia).",
    )

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    def __str__(self):
        return self.username


# --- MÓDULO 1: INVENTARIO ---


class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    nombre = models.CharField(max_length=150)
    material = models.CharField(max_length=100, help_text="Ej: 100% Algodón Pima")
    imagen = models.ImageField(
        upload_to="productos/",
        blank=True,
        null=True,
        help_text="Archivo de imagen (tiene prioridad sobre la URL en el catálogo).",
    )
    imagen_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text="URL de la foto del producto (vitrina) si no hay archivo subido.",
    )
    categoria = models.ForeignKey(
        Categoria, on_delete=models.PROTECT, related_name="productos"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    publicado = models.BooleanField(
        default=True,
        help_text="Si está desmarcado, el producto no aparece en la vitrina pública (oculto).",
    )

    def get_imagen(self):
        """Ruta relativa del archivo o URL externa (sin request)."""
        if self.imagen:
            return self.imagen.url
        return (self.imagen_url or "").strip()

    def url_imagen_para_catalogo(self, request):
        """URL absoluta para `<img>` en el catálogo."""
        if self.imagen:
            return request.build_absolute_uri(self.imagen.url)
        return (self.imagen_url or "").strip()

    def __str__(self):
        return self.nombre


class Variante(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name="variantes")
    sku_unico = models.CharField(max_length=50, unique=True)
    talla_etiqueta = models.CharField(max_length=20, help_text="Ej: 3-6M")

    meses_min = models.PositiveIntegerField(default=0)
    meses_max = models.PositiveIntegerField(default=0)

    color = models.CharField(max_length=50)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    visible = models.BooleanField(
        default=True,
        help_text="Si está desmarcado, esta variante no se muestra en el catálogo público.",
    )
    fecha_reposicion = models.DateField(
        null=True,
        blank=True,
        help_text="Fecha estimada de reposición (visible si la variante está agotada).",
    )

    @property
    def esta_agotado(self):
        return self.stock == 0

    def __str__(self):
        return f"{self.producto.nombre} - {self.talla_etiqueta} ({self.color})"


class Favorito(models.Model):
    """Favoritos por usuario (⭐) para rankings en el panel."""

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="favoritos"
    )
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name="marcado_favorito")
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("usuario", "producto"),
                name="uniq_favorito_usuario_producto",
            )
        ]
        ordering = ["-creado_en"]

    def __str__(self):
        return f"{self.usuario} → {self.producto}"


class Busqueda(models.Model):
    """Términos buscados en el catálogo (anon o autenticado) para estadísticas."""

    termino = models.CharField(max_length=100, db_index=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="busquedas_catalogo",
    )
    fecha = models.DateTimeField(auto_now_add=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ["-fecha"]

    def __str__(self):
        return self.termino[:40]


class ConfiguracionSitio(models.Model):
    """
    Configuración global del sitio (singleton lógico).
    Se edita desde el panel para evitar datos fijos en HTML.
    """

    nombre_tienda = models.CharField(max_length=150, default="Babyviip")

    instagram_usuario = models.CharField(max_length=100, blank=True, default="@babyviipcl")
    instagram_url = models.URLField(blank=True, default="https://www.instagram.com/babyviipcl/")

    facebook_nombre = models.CharField(
        max_length=150, blank=True, default="Grupo / página Babyviip"
    )
    facebook_url = models.URLField(
        blank=True,
        default="https://www.facebook.com/groups/1362338867173654/user/61587245798428/",
    )

    telefono = models.CharField(max_length=30, blank=True, default="+56 927493733")
    correo = models.EmailField(blank=True, default="babyviip8@gmail.com")

    direccion = models.CharField(
        max_length=255, blank=True, default="Gran Avenida 5234, local 17, San Miguel"
    )
    mapa_url = models.URLField(blank=True, default="https://share.google/C6HMTq54TXQDafIMq")
    whatsapp_url = models.URLField(blank=True, default="https://wa.me/56927493733")

    texto_bienvenida = models.TextField(
        blank=True,
        default="Ropa y accesorios para bebés desde recién nacidos hasta 3 años.",
    )

    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuración del sitio"
        verbose_name_plural = "Configuración del sitio"

    def __str__(self):
        return f"Configuración del sitio - {self.nombre_tienda}"


class Auditoria(models.Model):
    ACCIONES = [
        ("crear", "Crear"),
        ("editar", "Editar"),
        ("eliminar", "Eliminar"),
        ("login", "Inicio de sesión"),
        ("logout", "Cierre de sesión"),
        ("cambio_estado", "Cambio de estado"),
        ("exportar", "Exportación"),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="auditorias",
    )
    rol = models.CharField(max_length=60, blank=True)
    accion = models.CharField(max_length=30, choices=ACCIONES)
    modulo = models.CharField(max_length=100, blank=True)
    entidad = models.CharField(max_length=100, blank=True)
    entidad_id = models.CharField(max_length=50, blank=True)
    descripcion = models.TextField(blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    creado_en = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-creado_en"]

    def __str__(self):
        who = getattr(self.usuario, "username", None) or "—"
        return f"{who} · {self.accion} · {self.modulo}".strip()


class Conversacion(models.Model):
    ESTADOS = [
        ("abierta", "Abierta"),
        ("cerrada", "Cerrada"),
    ]

    cliente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="conversaciones",
        help_text="Usuario cliente que inicia la conversación.",
    )
    administrador_asignado = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="conversaciones_asignadas",
    )
    asunto = models.CharField(max_length=120, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default="abierta", db_index=True)
    creada_en = models.DateTimeField(auto_now_add=True, db_index=True)
    actualizada_en = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        ordering = ["-actualizada_en"]

    def __str__(self):
        return f"Conversación #{self.id} ({self.get_estado_display()})"


class Mensaje(models.Model):
    conversacion = models.ForeignKey(
        Conversacion, on_delete=models.CASCADE, related_name="mensajes"
    )
    emisor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="mensajes_enviados",
    )
    contenido = models.TextField()
    enviado_en = models.DateTimeField(auto_now_add=True, db_index=True)
    leido_por_admin = models.BooleanField(default=False, db_index=True)
    leido_por_cliente = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ["enviado_en"]

    def __str__(self):
        who = getattr(self.emisor, "username", None) or "—"
        return f"Msg {self.conversacion_id} · {who} · {self.enviado_en:%Y-%m-%d %H:%M}"


# --- MÓDULO 2: CLIENTES & VENTAS ---


class Cliente(models.Model):
    usuario = models.OneToOneField(
        "erp.Usuario",
        on_delete=models.CASCADE,
        related_name="perfil_cliente",
        null=True,
        blank=True,
    )
    rut = models.CharField(max_length=12, unique=True)
    nombre = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    contacto = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.nombre


class Venta(models.Model):
    ESTADOS_PEDIDO = [
        ("carrito", "Por comprar"),
        ("pendiente_pago", "Pendiente de pago"),
        ("pagado", "Comprado"),
        ("cancelado", "Pago cancelado"),
        ("revertida", "Revertida"),
    ]

    fecha = models.DateTimeField(auto_now_add=True)
    cliente = models.ForeignKey(
        Cliente, on_delete=models.SET_NULL, null=True, related_name="compras"
    )
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    estado = models.CharField(max_length=20, choices=ESTADOS_PEDIDO, default="carrito")

    es_simulacion = models.BooleanField(default=False, db_index=True)
    modo_simulacion = models.CharField(
        max_length=20,
        blank=True,
        choices=[
            ("sin_impacto", "Sin impacto"),
            ("temporal", "Temporal"),
            ("permanente", "Permanente"),
        ],
    )
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="ventas_creadas",
    )
    revertida_en = models.DateTimeField(null=True, blank=True)
    revertida_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="ventas_revertidas",
    )

    def __str__(self):
        return f"Venta #{self.id} - {self.fecha.strftime('%d/%m/%Y')}"


class DetalleVenta(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name="detalles")
    variante = models.ForeignKey(Variante, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField()
    precio_historico = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Precio al momento de la venta",
    )
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)

    def save(self, *args, **kwargs):
        self.subtotal = self.cantidad * self.precio_historico
        super().save(*args, **kwargs)
