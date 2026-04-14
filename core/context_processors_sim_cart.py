from erp.sim_cart import get_sim_cart


def carrito_simulado(request):
    """
    Contador global del carrito de simulación (panel).
    Se mantiene separado del carrito público.
    """
    try:
        cart = get_sim_cart(request.session)
        n = 0
        for _k, v in cart.items():
            try:
                n += int(v)
            except Exception:
                continue
        return {"sim_cart_count": max(0, n)}
    except Exception:
        return {"sim_cart_count": 0}

