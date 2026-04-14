"""
Datos del resumen del panel (dashboard). Compartido por la vista y las exportaciones.
"""

from datetime import timedelta

from django.conf import settings
from django.db.models import Count, Sum
from django.utils import timezone

from .models import Busqueda, Categoria, DetalleVenta, Favorito, Producto, Variante, Venta


def build_dashboard_context():
    """Contexto para `templates/panel/dashboard.html` y exportadores."""
    ahora = timezone.now()
    desde_30 = ahora - timedelta(days=30)
    total_productos = Producto.objects.count()
    total_categorias = Categoria.objects.count()
    umbral = getattr(settings, "STOCK_BAJO_UMBRAL", 5)
    productos_stock_bajo = (
        Producto.objects.filter(
            variantes__visible=True,
            variantes__stock__gt=0,
            variantes__stock__lt=umbral,
        )
        .distinct()
        .count()
    )
    variantes_agotadas = Variante.objects.filter(visible=True, stock=0).count()
    ventas_recientes = list(
        Venta.objects.select_related("cliente")
        .filter(es_simulacion=False)
        .order_by("-fecha")[:8]
    )
    ventas_30d = Venta.objects.filter(fecha__gte=desde_30, es_simulacion=False).count()
    top_vendidos = list(
        DetalleVenta.objects.values(
            "variante__producto__nombre",
            "variante__producto_id",
        )
        .annotate(total=Sum("cantidad"))
        .order_by("-total")[:8]
    )
    top_favoritos = list(
        Favorito.objects.values("producto__nombre", "producto_id")
        .annotate(total=Count("id"))
        .order_by("-total")[:8]
    )
    top_busquedas = list(
        Busqueda.objects.values("termino")
        .annotate(total=Count("id"))
        .order_by("-total")[:8]
    )
    chart_kpis = {
        "labels": ["Productos", "Categorías", "Prod. stock bajo", "Ventas 30 días"],
        "values": [
            total_productos,
            total_categorias,
            productos_stock_bajo,
            ventas_30d,
        ],
    }
    chart_vendidos = {
        "labels": [
            (row["variante__producto__nombre"] or "")[:28] for row in top_vendidos
        ],
        "values": [int(row["total"] or 0) for row in top_vendidos],
    }
    chart_favoritos = {
        "labels": [(row["producto__nombre"] or "")[:28] for row in top_favoritos],
        "values": [int(row["total"] or 0) for row in top_favoritos],
    }
    return {
        "total_productos": total_productos,
        "total_categorias": total_categorias,
        "productos_stock_bajo": productos_stock_bajo,
        "variantes_agotadas": variantes_agotadas,
        "ventas_recientes": ventas_recientes,
        "top_vendidos": top_vendidos,
        "top_favoritos": top_favoritos,
        "top_busquedas": top_busquedas,
        "chart_kpis": chart_kpis,
        "chart_vendidos": chart_vendidos,
        "chart_favoritos": chart_favoritos,
        "low_stock_threshold": getattr(settings, "STOCK_BAJO_UMBRAL", 5),
    }
