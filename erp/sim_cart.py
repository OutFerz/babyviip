SESSION_KEY = "babyviip_sim_cart"


def get_sim_cart(session):
    cart = session.get(SESSION_KEY)
    if not isinstance(cart, dict):
        cart = {}
        session[SESSION_KEY] = cart
    return cart


def set_sim_qty(session, variante_id: int, qty: int):
    cart = get_sim_cart(session)
    k = str(int(variante_id))
    if qty <= 0:
        cart.pop(k, None)
    else:
        cart[k] = int(qty)
    session[SESSION_KEY] = cart
    session.modified = True


def clear_sim_cart(session):
    session[SESSION_KEY] = {}
    session.modified = True

