from django.contrib import admin

from .models import (
    Categoria,
    Cliente,
    DetalleVenta,
    Producto,
    Variante,
    Venta,
)

admin.site.register(Categoria)
admin.site.register(Producto)
admin.site.register(Variante)
admin.site.register(Cliente)
admin.site.register(Venta)
admin.site.register(DetalleVenta)

