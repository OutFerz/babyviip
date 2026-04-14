"""Rutas del panel de catálogo. Incluidas en core.urls bajo prefix panel/."""

from django.urls import path

from . import panel_views

urlpatterns = [
    path("", panel_views.panel_inicio, name="panel_inicio"),
    path("api/variantes/", panel_views.panel_api_variantes, name="panel_api_variantes"),
    path("configuracion/", panel_views.panel_configuracion, name="panel_configuracion"),
    path("auditoria/", panel_views.panel_auditoria, name="panel_auditoria"),
    path("ventas/", panel_views.panel_ventas, name="panel_ventas"),
    path("mensajes/", panel_views.panel_mensajes, name="panel_mensajes"),
    path("mensajes/<int:pk>/", panel_views.panel_mensajes_detalle, name="panel_mensajes_detalle"),
    path("mensajes/<int:pk>/cerrar/", panel_views.panel_mensajes_cerrar, name="panel_mensajes_cerrar"),
    path("mensajes/<int:pk>/asignar/", panel_views.panel_mensajes_asignar, name="panel_mensajes_asignar"),
    path("simulador/compra/", panel_views.panel_simulador_compra, name="panel_simulador_compra"),
    path(
        "simulador/compra/<int:pk>/revertir/",
        panel_views.panel_simulador_revertir,
        name="panel_simulador_revertir",
    ),
    path(
        "auditoria/exportar/<str:fmt>/",
        panel_views.panel_auditoria_exportar,
        name="panel_auditoria_exportar",
    ),
    path(
        "exportar/grafico/<str:grafico>/<str:fmt>/",
        panel_views.panel_exportar_grafico,
        name="panel_exportar_grafico",
    ),
    path(
        "exportar/tabla/<str:tabla>/<str:fmt>/",
        panel_views.panel_exportar_tabla,
        name="panel_exportar_tabla",
    ),
    path(
        "exportar/<str:fmt>/",
        panel_views.panel_exportar,
        name="panel_exportar",
    ),
    path("productos/", panel_views.producto_listar, name="panel_productos"),
    path("productos/nuevo/", panel_views.producto_nuevo, name="panel_producto_nuevo"),
    path(
        "productos/<int:pk>/editar/",
        panel_views.producto_editar,
        name="panel_producto_editar",
    ),
    path(
        "productos/<int:pk>/eliminar/",
        panel_views.producto_eliminar,
        name="panel_producto_eliminar",
    ),
    path(
        "productos/<int:pk>/publicado/",
        panel_views.producto_toggle_publicado,
        name="panel_producto_toggle_publicado",
    ),
    path("categorias/", panel_views.categoria_listar, name="panel_categorias"),
    path("categorias/nueva/", panel_views.categoria_nueva, name="panel_categoria_nueva"),
    path(
        "categorias/<int:pk>/editar/",
        panel_views.categoria_editar,
        name="panel_categoria_editar",
    ),
    path(
        "categorias/<int:pk>/eliminar/",
        panel_views.categoria_eliminar,
        name="panel_categoria_eliminar",
    ),
]
