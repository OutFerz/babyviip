from erp.cart import cart_count


def carrito(request):
    try:
        return {"carrito_count": cart_count(request.session)}
    except Exception:
        return {"carrito_count": 0}

