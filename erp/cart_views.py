from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST, require_http_methods

from .auditoria import log_event
from .cart import calc_total, cart_count, clear_cart, get_cart, set_qty
from .models import Cliente, DetalleVenta, Variante, Venta


def _cart_lines(session):
    cart = get_cart(session)
    ids = []
    for k in cart.keys():
        if str(k).isdigit():
            ids.append(int(k))
    variantes = (
        Variante.objects.select_related("producto")
        .filter(id__in=ids, visible=True, producto__publicado=True)
    )
    by_id = {v.id: v for v in variantes}
    lines = []
    for k, qty in cart.items():
        if not str(k).isdigit():
            continue
        vid = int(k)
        v = by_id.get(vid)
        if not v:
            continue
        try:
            qty_i = int(qty)
        except Exception:
            qty_i = 0
        if qty_i <= 0:
            continue
        lines.append(
            {
                "variante": v,
                "cantidad": qty_i,
                "precio_unitario": Decimal(str(v.precio_unitario)),
                "subtotal": Decimal(str(v.precio_unitario)) * qty_i,
            }
        )
    total = calc_total(lines)
    return lines, total


@require_http_methods(["GET"])
def carrito_ver(request):
    lines, total = _cart_lines(request.session)
    return render(
        request,
        "carrito.html",
        {"lines": lines, "total": total, "cart_count": cart_count(request.session)},
    )


@require_POST
def carrito_add(request):
    vid = request.POST.get("variante_id")
    qty = request.POST.get("cantidad") or "1"
    try:
        vid_i = int(vid)
        qty_i = int(qty)
    except Exception:
        return JsonResponse({"ok": False}, status=400)
    qty_i = max(1, min(99, qty_i))
    # sumar si ya existe
    cart = get_cart(request.session)
    prev = int(cart.get(str(vid_i), 0) or 0)
    set_qty(request.session, vid_i, prev + qty_i)
    log_event(
        request=request,
        usuario=request.user if request.user.is_authenticated else None,
        accion="editar",
        modulo="carrito",
        entidad="Variante",
        entidad_id=str(vid_i),
        descripcion=f"Añadir al carrito (qty +{qty_i})",
    )
    return JsonResponse({"ok": True, "count": cart_count(request.session)})


@require_POST
def carrito_update(request):
    vid = request.POST.get("variante_id")
    qty = request.POST.get("cantidad") or "0"
    try:
        vid_i = int(vid)
        qty_i = int(qty)
    except Exception:
        return redirect("carrito")
    qty_i = max(0, min(99, qty_i))
    set_qty(request.session, vid_i, qty_i)
    return redirect("carrito")


@require_POST
def carrito_clear(request):
    clear_cart(request.session)
    return redirect("carrito")


@login_required(login_url="/accounts/login/")
@require_http_methods(["GET", "POST"])
def checkout(request):
    """
    Checkout simple (demo): crea venta real (estado=pendiente_pago por defecto)
    y descuenta stock al confirmar.
    """
    lines, total = _cart_lines(request.session)
    if not lines:
        messages.info(request, "Tu carrito está vacío.")
        return redirect("catalogo")

    # Perfil cliente (auto-creación mínima para demo si falta)
    perfil = getattr(request.user, "perfil_cliente", None)
    if not perfil:
        if not (request.user.email or "").strip():
            messages.error(
                request,
                "Tu cuenta no tiene correo. Actualiza tu usuario en /admin/ o registra una cuenta con email.",
            )
            return redirect("home")
        perfil = Cliente.objects.create(
            usuario=request.user,
            rut=f"SIM-{request.user.id}",
            nombre=request.user.get_username(),
            email=request.user.email.strip(),
            contacto="",
        )
        log_event(
            request=request,
            usuario=request.user,
            accion="crear",
            modulo="checkout",
            entidad="Cliente",
            entidad_id=str(perfil.pk),
            descripcion="Auto-crear perfil Cliente para checkout demo",
        )

    if request.method == "POST":
        # Validar stock
        insuf = []
        for ln in lines:
            v = ln["variante"]
            if int(v.stock) < int(ln["cantidad"]):
                insuf.append(ln)
        if insuf:
            for ln in insuf[:6]:
                v = ln["variante"]
                messages.error(
                    request,
                    f"Stock insuficiente: {v.producto.nombre} {v.talla_etiqueta}/{v.color} (SKU {v.sku_unico}).",
                )
            return redirect("carrito")

        with transaction.atomic():
            venta = Venta.objects.create(
                cliente=perfil,
                total=total,
                estado="pendiente_pago",
                es_simulacion=False,
                creado_por=request.user,
            )
            for ln in lines:
                v = ln["variante"]
                qty = int(ln["cantidad"])
                v.stock = int(v.stock) - qty
                v.save(update_fields=["stock"])
                DetalleVenta.objects.create(
                    venta=venta,
                    variante=v,
                    cantidad=qty,
                    precio_historico=v.precio_unitario,
                )

        clear_cart(request.session)
        log_event(
            request=request,
            usuario=request.user,
            accion="crear",
            modulo="checkout",
            entidad="Venta",
            entidad_id=str(venta.pk),
            descripcion="Checkout: crear venta desde carrito",
        )
        messages.success(request, f"Compra registrada. Venta #{venta.id}.")
        return redirect(reverse("panel_ventas") + f"?q={venta.id}")

    return render(
        request,
        "checkout.html",
        {"lines": lines, "total": total, "perfil": perfil},
    )

