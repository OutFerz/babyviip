from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import (
    Busqueda,
    Categoria,
    Cliente,
    ConfiguracionSitio,
    DetalleVenta,
    Favorito,
    Producto,
    Usuario,
    Variante,
    Venta,
)


@admin.register(Usuario)
class UsuarioAdmin(BaseUserAdmin):
    list_display = (
        "username",
        "email",
        "is_staff",
        "is_active",
        "es_cliente",
        "es_administrador_tienda",
    )
    list_filter = ("is_staff", "is_superuser", "es_cliente", "es_administrador_tienda")
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Roles Babyviip", {"fields": ("es_cliente", "es_administrador_tienda")}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (None, {"fields": ("es_cliente", "es_administrador_tienda")}),
    )


admin.site.register(Categoria)


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "categoria", "publicado", "fecha_creacion")
    list_filter = ("publicado", "categoria")
    search_fields = ("nombre", "material")
@admin.register(Variante)
class VarianteAdmin(admin.ModelAdmin):
    list_display = (
        "sku_unico",
        "producto",
        "talla_etiqueta",
        "stock",
        "visible",
        "fecha_reposicion",
    )
    list_filter = ("visible", "producto__categoria")
    search_fields = ("sku_unico", "producto__nombre")


@admin.register(Favorito)
class FavoritoAdmin(admin.ModelAdmin):
    list_display = ("usuario", "producto", "creado_en")
    list_filter = ("creado_en",)


@admin.register(Busqueda)
class BusquedaAdmin(admin.ModelAdmin):
    list_display = ("termino", "usuario", "ip", "fecha")
    list_filter = ("fecha",)
    search_fields = ("termino", "ip")


@admin.register(ConfiguracionSitio)
class ConfiguracionSitioAdmin(admin.ModelAdmin):
    list_display = ("nombre_tienda", "telefono", "correo", "actualizado_en")
admin.site.register(Cliente)
admin.site.register(Venta)
admin.site.register(DetalleVenta)
