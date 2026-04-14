from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch, Q
from django.middleware.csrf import get_token
from django.shortcuts import redirect, render

from django.urls import reverse

from erp.models import Categoria, Favorito, Producto, Variante, Venta


def _serialize_catalogo(request, categorias):
    """JSON para búsqueda/filtros en cliente (templates/catalogo.html + static/js/catalogo.js)."""
    out = []
    for c in categorias:
        productos = []
        for p in c.productos.all():
            variantes = []
            for v in p.variantes.all():
                variantes.append(
                    {
                        "id": v.id,
                        "sku": v.sku_unico,
                        "talla": v.talla_etiqueta,
                        "meses_min": v.meses_min,
                        "meses_max": v.meses_max,
                        "color": v.color,
                        "precio": str(v.precio_unitario),
                        "stock": v.stock,
                        "agotado": v.stock == 0,
                        "fecha_reposicion": v.fecha_reposicion.isoformat()
                        if v.fecha_reposicion
                        else "",
                    }
                )
            productos.append(
                {
                    "id": p.id,
                    "categoria_id": c.id,
                    "nombre": p.nombre,
                    "material": p.material,
                    "imagen_url": p.url_imagen_para_catalogo(request),
                    "variantes": variantes,
                }
            )
        out.append(
            {
                "id": c.id,
                "nombre": c.nombre,
                "descripcion": c.descripcion or "",
                "productos": productos,
            }
        )
    return out


def home(request):
    """
    Página de bienvenida (visitantes sin sesión).

    Renderiza: templates/home.html
    Contexto global: ``contacto`` (core.context_processors.contacto).
    Estilos: static/css/home.css · static/css/site_nav.css · Script: static/js/home.js
    """
    return render(request, "home.html")


def catalogo(request):
    """
    Vitrina / inventario ERP: modelos Categoria → Producto → Variante.

    Renderiza: templates/catalogo.html
    Consulta: prefetch de productos y variantes por categoría.
    Estilos: static/css/catalogo.css · static/css/site_nav.css · Script: static/js/catalogo.js
    """
    categorias = (
        Categoria.objects.order_by("nombre")
        .prefetch_related(
            Prefetch(
                "productos",
                queryset=Producto.objects.filter(publicado=True)
                .order_by("nombre")
                .prefetch_related(
                    Prefetch(
                        "variantes",
                        queryset=Variante.objects.filter(visible=True).order_by(
                            "talla_etiqueta", "color"
                        ),
                    )
                ),
            )
        )
    )
    catalogo_data = (
        _serialize_catalogo(request, categorias) if categorias else []
    )
    favoritos_ids = []
    if request.user.is_authenticated:
        favoritos_ids = list(
            Favorito.objects.filter(usuario=request.user).values_list(
                "producto_id", flat=True
            )
        )
    catalogo_config = {
        "userAuth": request.user.is_authenticated,
        "favoritosServidor": favoritos_ids,
        "csrf": get_token(request),
    }
    return render(
        request,
        "catalogo.html",
        {
            "categorias": categorias,
            "catalogo_data": catalogo_data,
            "catalogo_config": catalogo_config,
        },
    )


def _puede_ver_ventas(user):
    return user.is_authenticated and (
        user.is_staff or getattr(user, "es_administrador_tienda", False)
    )


@login_required(login_url="/accounts/login/")
def ventas_clientes(request):
    """
    Resumen de ventas (Cliente / Venta / DetalleVenta). Solo staff o administrador de tienda.

    Renderiza: templates/ventas.html
    Estilos: static/css/ventas.css · static/css/site_nav.css · Script: static/js/ventas.js
    """
    # Ruta legacy: la vista operativa vive en el panel.
    if not request.user.is_authenticated:
        return redirect("/accounts/login/")
    if not _puede_ver_ventas(request.user):
        messages.warning(request, "No tienes permiso para ver ventas.")
        return redirect("home")
    # Mantener querystring (sim/q/estado) al redirigir
    target = reverse("panel_ventas")
    qs = request.META.get("QUERY_STRING") or ""
    if qs:
        target = f"{target}?{qs}"
    return redirect(target)
