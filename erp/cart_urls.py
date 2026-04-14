from django.urls import path

from . import cart_views

urlpatterns = [
    path("", cart_views.carrito_ver, name="carrito"),
    path("add/", cart_views.carrito_add, name="carrito_add"),
    path("update/", cart_views.carrito_update, name="carrito_update"),
    path("clear/", cart_views.carrito_clear, name="carrito_clear"),
    path("checkout/", cart_views.checkout, name="checkout"),
]

