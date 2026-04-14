from decimal import Decimal


SESSION_KEY = "babyviip_cart"


def get_cart(session):
    cart = session.get(SESSION_KEY)
    if not isinstance(cart, dict):
        cart = {}
        session[SESSION_KEY] = cart
    return cart


def cart_count(session) -> int:
    cart = get_cart(session)
    n = 0
    for _k, v in cart.items():
        try:
            n += int(v)
        except Exception:
            continue
    return max(0, n)


def set_qty(session, variante_id: int, qty: int):
    cart = get_cart(session)
    k = str(int(variante_id))
    if qty <= 0:
        cart.pop(k, None)
    else:
        cart[k] = int(qty)
    session[SESSION_KEY] = cart
    session.modified = True


def clear_cart(session):
    session[SESSION_KEY] = {}
    session.modified = True


def calc_total(lines) -> Decimal:
    total = Decimal("0")
    for ln in lines:
        total += (ln["precio_unitario"] * ln["cantidad"])
    return total

