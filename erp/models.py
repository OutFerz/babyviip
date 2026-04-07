from django.core.validators import MinValueValidator
from django.db import models


# --- MÓDULO 1: INVENTARIO ---


class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    nombre = models.CharField(max_length=150)
    material = models.CharField(max_length=100, help_text="Ej: 100% Algodón Pima")
    categoria = models.ForeignKey(
        Categoria, on_delete=models.PROTECT, related_name="productos"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre


class Variante(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name="variantes")
    sku_unico = models.CharField(max_length=50, unique=True)
    talla_etiqueta = models.CharField(max_length=20, help_text="Ej: 3-6M")

    # Rango de meses para filtros técnicos en PostgreSQL
    meses_min = models.PositiveIntegerField(default=0)
    meses_max = models.PositiveIntegerField(default=0)

    color = models.CharField(max_length=50)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0, validators=[MinValueValidator(0)])

    def __str__(self):
        return f"{self.producto.nombre} - {self.talla_etiqueta} ({self.color})"


# --- MÓDULO 2: VENTAS & CLIENTES ---


class Cliente(models.Model):
    rut = models.CharField(max_length=12, unique=True)  # Formato chileno: 12.345.678-9
    nombre = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    contacto = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.nombre


class Venta(models.Model):
    fecha = models.DateTimeField(auto_now_add=True)
    cliente = models.ForeignKey(
        Cliente, on_delete=models.SET_NULL, null=True, related_name="compras"
    )
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

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

