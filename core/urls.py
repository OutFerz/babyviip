"""
URL configuration for core project.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from erp.auth_views import BabyviipLoginView, BabyviipLogoutView, registro
from erp.catalog_api import busqueda_log, favorito_toggle

from .views import catalogo, home, ventas_clientes

urlpatterns = [
    path("", home, name="home"),
    path("catalogo/", catalogo, name="catalogo"),
    path("api/catalogo/favorito/", favorito_toggle, name="catalogo_favorito_toggle"),
    path("api/catalogo/busqueda/", busqueda_log, name="catalogo_busqueda_log"),
    path("carrito/", include("erp.cart_urls")),
    path("panel/", include("erp.panel_urls")),
    path("mensajes/", include("erp.chat_urls")),
    path("ventas/", ventas_clientes, name="ventas_clientes"),
    path("accounts/login/", BabyviipLoginView.as_view(), name="login"),
    path("accounts/logout/", BabyviipLogoutView.as_view(), name="logout"),
    path("accounts/registro/", registro, name="registro"),
    path("admin/", admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
