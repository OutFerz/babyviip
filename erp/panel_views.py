"""
Panel de gestión del catálogo (staff o es_administrador_tienda).
Plantillas: templates/panel/*.html · CSS: static/css/panel.css · JS: static/js/panel.js
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import ProtectedError
from django.db.models import Q
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.utils import timezone

from .dashboard_context import build_dashboard_context
from .dashboard_export import (
    CHART_META,
    TABLA_META,
    export_chart_csv,
    export_chart_html,
    export_chart_pdf,
    export_chart_xlsx,
    export_dashboard_csv,
    export_dashboard_html,
    export_dashboard_pdf,
    export_dashboard_xlsx,
    export_tabla_csv,
    export_tabla_html,
    export_tabla_pdf,
    export_tabla_xlsx,
)
from .models import (
    Auditoria,
    Busqueda,
    Categoria,
    Cliente,
    Conversacion,
    ConfiguracionSitio,
    DetalleVenta,
    Favorito,
    Mensaje,
    Producto,
    Variante,
    Venta,
)
from .panel_forms import (
    CategoriaPanelForm,
    ConfiguracionSitioForm,
    ProductoPanelForm,
    SimuladorCompraForm,
    SimuladorLineaForm,
    VarianteFormSet,
)
from .auditoria import log_event
from .auditoria_export import (
    export_auditoria_csv,
    export_auditoria_html,
    export_auditoria_pdf,
    export_auditoria_xlsx,
)
from .sim_cart import clear_sim_cart, get_sim_cart, set_sim_qty


def _puede_panel(user):
    return user.is_authenticated and (
        user.is_staff or getattr(user, "es_administrador_tienda", False)
    )


def _puede_auditoria(user):
    return user.is_authenticated and (
        user.is_staff
        or getattr(user, "es_administrador_tienda", False)
        or getattr(user, "es_empleado", False)
    )


def _requiere_auditoria(request):
    if not request.user.is_authenticated:
        return redirect("/accounts/login/")
    if not _puede_auditoria(request.user):
        messages.warning(request, "No tienes permiso para la auditoría.")
        return redirect("home")
    return None


def _requiere_panel(request):
    if not request.user.is_authenticated:
        return redirect("/accounts/login/")
    if not _puede_panel(request.user):
        messages.warning(
            request,
            "No tienes permiso para el panel de catálogo.",
        )
        return redirect("home")
    return None


@login_required(login_url="/accounts/login/")
def panel_inicio(request):
    """Resumen operativo: KPIs, rankings y accesos rápidos."""
    redir = _requiere_panel(request)
    if redir:
        return redir
    return render(request, "panel/dashboard.html", build_dashboard_context())


@login_required(login_url="/accounts/login/")
def panel_exportar(request, fmt):
    """Descarga del resumen del panel: csv, xlsx, pdf, html."""
    redir = _requiere_panel(request)
    if redir:
        return redir
    ctx = build_dashboard_context()
    fmt = (fmt or "").lower()
    if fmt == "csv":
        log_event(request=request, usuario=request.user, accion="exportar", modulo="panel", entidad="Dashboard", descripcion="Exportar informe completo (CSV)")
        return export_dashboard_csv(ctx)
    if fmt in ("xlsx", "excel"):
        log_event(request=request, usuario=request.user, accion="exportar", modulo="panel", entidad="Dashboard", descripcion="Exportar informe completo (XLSX)")
        return export_dashboard_xlsx(ctx)
    if fmt == "pdf":
        log_event(request=request, usuario=request.user, accion="exportar", modulo="panel", entidad="Dashboard", descripcion="Exportar informe completo (PDF)")
        return export_dashboard_pdf(ctx)
    if fmt == "html":
        log_event(request=request, usuario=request.user, accion="exportar", modulo="panel", entidad="Dashboard", descripcion="Exportar informe completo (HTML)")
        return export_dashboard_html(ctx)
    messages.error(request, "Formato de exportación no reconocido.")
    return redirect("panel_inicio")


@login_required(login_url="/accounts/login/")
def panel_exportar_grafico(request, grafico, fmt):
    """Un solo gráfico (datos label/valor): csv, xlsx, pdf, html."""
    redir = _requiere_panel(request)
    if redir:
        return redir
    grafico = (grafico or "").lower()
    fmt = (fmt or "").lower()
    if grafico not in CHART_META:
        messages.error(request, "Gráfico no reconocido.")
        return redirect("panel_inicio")
    ctx = build_dashboard_context()
    dispatch = {
        "csv": export_chart_csv,
        "xlsx": export_chart_xlsx,
        "excel": export_chart_xlsx,
        "pdf": export_chart_pdf,
        "html": export_chart_html,
    }
    fn = dispatch.get(fmt)
    if not fn:
        messages.error(request, "Formato no reconocido.")
        return redirect("panel_inicio")
    out = fn(ctx, grafico)
    if out is None:
        messages.error(request, "No se pudo generar la exportación.")
        return redirect("panel_inicio")
    log_event(
        request=request,
        usuario=request.user,
        accion="exportar",
        modulo="panel",
        entidad="Grafico",
        entidad_id=grafico,
        descripcion=f"Exportar gráfico {grafico} ({fmt})",
    )
    return out


@login_required(login_url="/accounts/login/")
def panel_exportar_tabla(request, tabla, fmt):
    """Un bloque de tabla del dashboard: csv, xlsx, pdf, html."""
    redir = _requiere_panel(request)
    if redir:
        return redir
    tabla = (tabla or "").lower()
    fmt = (fmt or "").lower()
    if tabla not in TABLA_META:
        messages.error(request, "Tabla no reconocida.")
        return redirect("panel_inicio")
    ctx = build_dashboard_context()
    dispatch = {
        "csv": export_tabla_csv,
        "xlsx": export_tabla_xlsx,
        "excel": export_tabla_xlsx,
        "pdf": export_tabla_pdf,
        "html": export_tabla_html,
    }
    fn = dispatch.get(fmt)
    if not fn:
        messages.error(request, "Formato no reconocido.")
        return redirect("panel_inicio")
    out = fn(ctx, tabla)
    if out is None:
        messages.error(request, "No se pudo generar la exportación.")
        return redirect("panel_inicio")
    log_event(
        request=request,
        usuario=request.user,
        accion="exportar",
        modulo="panel",
        entidad="Tabla",
        entidad_id=tabla,
        descripcion=f"Exportar tabla {tabla} ({fmt})",
    )
    return out


@login_required(login_url="/accounts/login/")
@require_http_methods(["GET", "POST"])
def panel_configuracion(request):
    """Configuración global (contacto/redes/local) editable desde el panel."""
    redir = _requiere_panel(request)
    if redir:
        return redir

    cfg = ConfiguracionSitio.objects.order_by("id").first()
    if cfg is None:
        cfg = ConfiguracionSitio.objects.create()

    if request.method == "POST":
        form = ConfiguracionSitioForm(request.POST, instance=cfg)
        if form.is_valid():
            form.save()
            log_event(
                request=request,
                usuario=request.user,
                accion="editar",
                modulo="sitio",
                entidad="ConfiguracionSitio",
                entidad_id=str(cfg.pk),
                descripcion="Editar configuración del sitio (contacto/redes/local)",
            )
            messages.success(request, "Configuración actualizada.")
            return redirect("panel_configuracion")
    else:
        form = ConfiguracionSitioForm(instance=cfg)

    return render(
        request,
        "panel/configuracion_form.html",
        {"form": form, "titulo": "Configuración del sitio"},
    )


@login_required(login_url="/accounts/login/")
def panel_auditoria(request):
    """
    Auditoría del sistema.
    - Admin/staff: ve todo.
    - Empleado: solo ve sus propios registros.
    """
    redir = _requiere_auditoria(request)
    if redir:
        return redir

    qs = Auditoria.objects.select_related("usuario").all()
    is_admin = request.user.is_staff or getattr(request.user, "es_administrador_tienda", False)
    if not is_admin:
        qs = qs.filter(usuario=request.user)

    q = (request.GET.get("q") or "").strip()
    accion = (request.GET.get("accion") or "").strip().lower()
    modulo = (request.GET.get("modulo") or "").strip()
    usuario = (request.GET.get("usuario") or "").strip()
    desde = (request.GET.get("desde") or "").strip()
    hasta = (request.GET.get("hasta") or "").strip()

    if q:
        qs = qs.filter(
            Q(descripcion__icontains=q)
            | Q(modulo__icontains=q)
            | Q(entidad__icontains=q)
            | Q(entidad_id__icontains=q)
            | Q(usuario__username__icontains=q)
            | Q(accion__icontains=q)
            | Q(rol__icontains=q)
        )
    if accion:
        qs = qs.filter(accion=accion)
    if modulo:
        qs = qs.filter(modulo__icontains=modulo)
    if usuario and is_admin:
        qs = qs.filter(usuario__username__icontains=usuario)

    # Fechas (YYYY-MM-DD) sobre creado_en (timezone-aware)
    if desde:
        try:
            d = timezone.datetime.fromisoformat(desde).date()
            qs = qs.filter(creado_en__date__gte=d)
        except ValueError:
            pass
    if hasta:
        try:
            d = timezone.datetime.fromisoformat(hasta).date()
            qs = qs.filter(creado_en__date__lte=d)
        except ValueError:
            pass

    # Paginación simple
    limit = 200
    auditorias = list(qs[:limit])

    acciones = Auditoria.ACCIONES
    return render(
        request,
        "panel/auditoria_list.html",
        {
            "auditorias": auditorias,
            "acciones": acciones,
            "is_admin_auditoria": is_admin,
            "filtros": {
                "q": q,
                "accion": accion,
                "modulo": modulo,
                "usuario": usuario,
                "desde": desde,
                "hasta": hasta,
            },
            "limit": limit,
        },
    )


@login_required(login_url="/accounts/login/")
def panel_auditoria_exportar(request, fmt):
    """Exporta auditoría (filtrada según permisos y querystring)."""
    redir = _requiere_auditoria(request)
    if redir:
        return redir

    qs = Auditoria.objects.select_related("usuario").all()
    is_admin = request.user.is_staff or getattr(request.user, "es_administrador_tienda", False)
    if not is_admin:
        qs = qs.filter(usuario=request.user)

    q = (request.GET.get("q") or "").strip()
    accion = (request.GET.get("accion") or "").strip().lower()
    modulo = (request.GET.get("modulo") or "").strip()
    usuario = (request.GET.get("usuario") or "").strip()
    desde = (request.GET.get("desde") or "").strip()
    hasta = (request.GET.get("hasta") or "").strip()

    if q:
        qs = qs.filter(
            Q(descripcion__icontains=q)
            | Q(modulo__icontains=q)
            | Q(entidad__icontains=q)
            | Q(entidad_id__icontains=q)
            | Q(usuario__username__icontains=q)
            | Q(accion__icontains=q)
            | Q(rol__icontains=q)
        )
    if accion:
        qs = qs.filter(accion=accion)
    if modulo:
        qs = qs.filter(modulo__icontains=modulo)
    if usuario and is_admin:
        qs = qs.filter(usuario__username__icontains=usuario)
    if desde:
        try:
            d = timezone.datetime.fromisoformat(desde).date()
            qs = qs.filter(creado_en__date__gte=d)
        except ValueError:
            pass
    if hasta:
        try:
            d = timezone.datetime.fromisoformat(hasta).date()
            qs = qs.filter(creado_en__date__lte=d)
        except ValueError:
            pass

    qs = qs[:2000]
    fmt = (fmt or "").lower()
    dispatch = {
        "csv": export_auditoria_csv,
        "xlsx": export_auditoria_xlsx,
        "excel": export_auditoria_xlsx,
        "pdf": export_auditoria_pdf,
        "html": export_auditoria_html,
    }
    fn = dispatch.get(fmt)
    if not fn:
        messages.error(request, "Formato no reconocido.")
        return redirect("panel_auditoria")

    out = fn(qs)
    log_event(
        request=request,
        usuario=request.user,
        accion="exportar",
        modulo="auditoria",
        entidad="Auditoria",
        descripcion=f"Exportar auditoría ({fmt})",
    )
    return out


@login_required(login_url="/accounts/login/")
@require_http_methods(["GET", "POST"])
def panel_simulador_compra(request):
    """
    Simulador de compra (panel).
    - sin_impacto: no crea venta ni descuenta stock.
    - temporal: crea venta simulada y descuenta stock (reversible).
    - permanente: crea venta real y descuenta stock.
    """
    redir = _requiere_panel(request)
    if redir:
        return redir

    venta_temporal = None

    if request.method == "POST":
        form = SimuladorCompraForm(request.POST)
        line_count = form.data.get("line_count") or 3
        try:
            line_count = int(line_count)
        except (TypeError, ValueError):
            line_count = 3
        line_count = max(1, min(30, line_count))
        lineas = [
            SimuladorLineaForm(request.POST, prefix=f"l{i}")
            for i in range(1, line_count + 1)
        ]
        any_line_errors = False
        items = []
        for lf in lineas:
            if not lf.is_valid():
                # Puede ser fila vacía o error real; marcamos para feedback en template
                if lf.errors:
                    any_line_errors = True
                continue
            v = lf.cleaned_data.get("variante")
            qty = lf.cleaned_data.get("cantidad")
            if not v:
                continue
            try:
                qty_i = int(qty or 0)
            except Exception:
                qty_i = 0
            if qty_i <= 0:
                continue
            items.append((v, qty_i))

        if form.is_valid() and not any_line_errors:
            modo = form.cleaned_data["modo"]
            estado = form.cleaned_data["estado"]
            cliente = form.cleaned_data.get("cliente")

            if not items:
                messages.error(
                    request, "Agrega al menos una variante con cantidad para ejecutar."
                )
                return render(
                    request,
                    "panel/simulador_compra.html",
                    {"form": form, "lineas": lineas, "venta_temporal": None},
                )

            merged = {}
            for v, qty in items:
                prev = merged.get(v.id)
                merged[v.id] = (v, (prev[1] if prev else 0) + qty)
            items = list(merged.values())

            # Persistir carrito de simulación separado del público
            clear_sim_cart(request.session)
            for v, qty in items:
                set_sim_qty(request.session, v.id, qty)

            total = sum((v.precio_unitario * qty for v, qty in items), 0)

            if modo == "sin_impacto":
                log_event(
                    request=request,
                    usuario=request.user,
                    accion="exportar",
                    modulo="simulador",
                    entidad="Simulacion",
                    descripcion=f"Simulación sin impacto ({estado}) · total={total}",
                )
                messages.success(request, f"Simulación sin impacto OK. Total: ${total}.")
                return redirect("panel_simulador_compra")

            # Validación de stock (protege modo temporal/permanente)
            insuf = []
            for v, qty in items:
                if int(v.stock) < int(qty):
                    insuf.append((v, qty, int(v.stock)))
            if insuf:
                for v, qty, stock in insuf[:6]:
                    messages.error(
                        request,
                        f"Stock insuficiente: {v.producto.nombre} ({v.talla_etiqueta}/{v.color}) "
                        f"SKU {v.sku_unico} · solicitado {qty} · stock {stock}.",
                    )
                if len(insuf) > 6:
                    messages.error(request, "Hay más variantes con stock insuficiente.")
                # re-render con los valores actuales
                return render(
                    request,
                    "panel/simulador_compra.html",
                    {"form": form, "lineas": lineas, "venta_temporal": None},
                )

            with transaction.atomic():
                es_sim = modo == "temporal"
                venta = Venta.objects.create(
                    cliente=cliente,
                    total=total,
                    estado=estado,
                    es_simulacion=es_sim,
                    modo_simulacion=modo,
                    creado_por=request.user,
                )
                for v, qty in items:
                    # ya validado, por lo tanto no debería quedar negativo
                    v.stock = int(v.stock) - int(qty)
                    v.save(update_fields=["stock"])
                    DetalleVenta.objects.create(
                        venta=venta,
                        variante=v,
                        cantidad=qty,
                        precio_historico=v.precio_unitario,
                    )

            if modo == "temporal":
                log_event(
                    request=request,
                    usuario=request.user,
                    accion="crear",
                    modulo="simulador",
                    entidad="Venta",
                    entidad_id=str(venta.pk),
                    descripcion="Crear venta temporal (simulada) desde simulador",
                )
                messages.success(request, f"Venta temporal creada (simulación) #{venta.id}.")
                venta_temporal = venta
                clear_sim_cart(request.session)
            else:
                log_event(
                    request=request,
                    usuario=request.user,
                    accion="crear",
                    modulo="simulador",
                    entidad="Venta",
                    entidad_id=str(venta.pk),
                    descripcion="Crear venta permanente (real) desde simulador",
                )
                messages.success(request, f"Venta permanente creada (real) #{venta.id}.")
                clear_sim_cart(request.session)
                return redirect("ventas_clientes")
        else:
            if not form.is_valid():
                messages.error(request, "Revisa los campos del formulario (modo/estado).")
            if any_line_errors:
                messages.error(request, "Revisa las filas con errores (variante/cantidad).")
    else:
        form = SimuladorCompraForm()
        sim_cart = get_sim_cart(request.session)
        # Pre-cargar desde carrito de simulación si existe
        pairs = []
        for k, qty in sim_cart.items():
            if str(k).isdigit():
                try:
                    pairs.append((int(k), int(qty)))
                except Exception:
                    continue
        pairs = pairs[:10]
        if pairs:
            form.initial["line_count"] = max(3, len(pairs))
            lineas = []
            for i in range(1, form.initial["line_count"] + 1):
                if i <= len(pairs):
                    vid, q0 = pairs[i - 1]
                    lineas.append(
                        SimuladorLineaForm(
                            prefix=f"l{i}",
                            initial={"variante": vid, "cantidad": max(1, q0)},
                        )
                    )
                else:
                    lineas.append(SimuladorLineaForm(prefix=f"l{i}"))
        else:
            lineas = [SimuladorLineaForm(prefix=f"l{i}") for i in range(1, 6)]
            form.initial["line_count"] = len(lineas)

    sim_cart = get_sim_cart(request.session)
    sim_count = 0
    for _k, v in sim_cart.items():
        try:
            sim_count += int(v)
        except Exception:
            continue
    return render(
        request,
        "panel/simulador_compra.html",
        {
            "form": form,
            "lineas": lineas,
            "venta_temporal": venta_temporal,
            "sim_cart_count": max(0, sim_count),
        },
    )


@login_required(login_url="/accounts/login/")
@require_POST
def panel_simulador_revertir(request, pk):
    """Revertir una venta temporal simulada: reponer stock y marcar revertida."""
    redir = _requiere_panel(request)
    if redir:
        return redir
    venta = get_object_or_404(Venta, pk=pk)
    if not (venta.es_simulacion and venta.modo_simulacion == "temporal"):
        messages.error(request, "Solo se pueden revertir ventas temporales simuladas.")
        return redirect("panel_simulador_compra")
    if venta.estado == "revertida":
        messages.info(request, "Esta simulación ya fue revertida.")
        return redirect("panel_simulador_compra")

    is_admin = request.user.is_staff or getattr(request.user, "es_administrador_tienda", False)
    if not is_admin and venta.creado_por_id != request.user.id:
        messages.error(request, "No puedes revertir simulaciones de otros usuarios.")
        return redirect("panel_simulador_compra")

    with transaction.atomic():
        for d in venta.detalles.select_related("variante").all():
            v = d.variante
            v.stock = int(v.stock) + int(d.cantidad)
            v.save(update_fields=["stock"])
        venta.estado = "revertida"
        venta.revertida_en = timezone.now()
        venta.revertida_por = request.user
        venta.save(update_fields=["estado", "revertida_en", "revertida_por"])

    log_event(
        request=request,
        usuario=request.user,
        accion="cambio_estado",
        modulo="simulador",
        entidad="Venta",
        entidad_id=str(venta.pk),
        descripcion="Revertir venta temporal simulada (reponer stock)",
    )
    messages.success(request, f"Simulación revertida. Venta #{venta.id}. Stock repuesto.")
    return redirect("panel_simulador_compra")

@login_required(login_url="/accounts/login/")
def panel_api_variantes(request):
    """Autocomplete de variantes para el simulador (SKU/nombre/talla/color)."""
    redir = _requiere_panel(request)
    if redir:
        return JsonResponse({"ok": False}, status=403)

    q = (request.GET.get("q") or "").strip()
    if len(q) < 2:
        return JsonResponse({"ok": True, "items": []})

    qs = (
        Variante.objects.select_related("producto")
        .filter(
            Q(sku_unico__icontains=q)
            | Q(producto__nombre__icontains=q)
            | Q(color__icontains=q)
            | Q(talla_etiqueta__icontains=q)
        )
        .order_by("producto__nombre", "talla_etiqueta", "color")[:12]
    )

    items = []
    for v in qs:
        items.append(
            {
                "id": v.id,
                "sku": v.sku_unico,
                "producto": v.producto.nombre,
                "talla": v.talla_etiqueta,
                "color": v.color,
                "stock": int(v.stock or 0),
                "precio": str(v.precio_unitario),
                "label": f"{v.producto.nombre} — {v.talla_etiqueta} — {v.color} — stock {int(v.stock or 0)} — ${v.precio_unitario}",
            }
        )
    return JsonResponse({"ok": True, "items": items})


@login_required(login_url="/accounts/login/")
def panel_mensajes(request):
    """Bandeja de conversaciones (admin ve todo; empleado solo asignadas o propias)."""
    redir = _requiere_panel(request)
    if redir:
        return redir

    is_admin = request.user.is_staff or getattr(request.user, "es_administrador_tienda", False)
    qs = (
        Conversacion.objects.select_related("cliente", "administrador_asignado")
        .annotate(
            unread_count=Count(
                "mensajes",
                filter=Q(mensajes__leido_por_admin=False)
                & ~Q(mensajes__emisor=request.user),
            )
        )
        .all()
    )
    if not is_admin:
        qs = qs.filter(administrador_asignado=request.user)

    q = (request.GET.get("q") or "").strip()
    estado = (request.GET.get("estado") or "").strip()
    unread = (request.GET.get("unread") or "").strip()
    asignacion = (request.GET.get("asignacion") or "").strip()

    if q:
        qs = qs.filter(
            Q(asunto__icontains=q)
            | Q(cliente__username__icontains=q)
            | Q(mensajes__contenido__icontains=q)
        ).distinct()
    if estado in ("abierta", "cerrada"):
        qs = qs.filter(estado=estado)
    if unread == "1":
        qs = qs.filter(unread_count__gt=0)
    if asignacion and is_admin:
        if asignacion == "mias":
            qs = qs.filter(administrador_asignado=request.user)
        elif asignacion == "sin_asignar":
            qs = qs.filter(administrador_asignado__isnull=True)

    convs = list(qs.order_by("-actualizada_en")[:200])
    return render(
        request,
        "panel/mensajes_list.html",
        {
            "convs": convs,
            "is_admin": is_admin,
            "f": {"q": q, "estado": estado, "unread": unread, "asignacion": asignacion},
        },
    )


@login_required(login_url="/accounts/login/")
@require_http_methods(["GET", "POST"])
def panel_mensajes_detalle(request, pk):
    redir = _requiere_panel(request)
    if redir:
        return redir

    is_admin = request.user.is_staff or getattr(request.user, "es_administrador_tienda", False)
    conv = get_object_or_404(
        Conversacion.objects.select_related("cliente", "administrador_asignado"),
        pk=pk,
    )
    if not is_admin and conv.administrador_asignado_id != request.user.id:
        messages.error(request, "No tienes permiso para ver esta conversación.")
        return redirect("panel_mensajes")

    if request.method == "POST":
        if conv.estado != "abierta":
            messages.error(request, "La conversación está cerrada.")
            return redirect("panel_mensajes_detalle", pk=conv.pk)
        contenido = (request.POST.get("contenido") or "").strip()
        if len(contenido) < 1:
            messages.error(request, "Mensaje vacío.")
            return redirect("panel_mensajes_detalle", pk=conv.pk)
        Mensaje.objects.create(
            conversacion=conv,
            emisor=request.user,
            contenido=contenido,
            leido_por_admin=True,
            leido_por_cliente=False,
        )
        log_event(
            request=request,
            usuario=request.user,
            accion="crear",
            modulo="chat",
            entidad="Mensaje",
            entidad_id=str(conv.pk),
            descripcion="Admin envía mensaje",
        )
        return redirect("panel_mensajes_detalle", pk=conv.pk)

    # marcar leído por admin los mensajes del cliente
    Mensaje.objects.filter(conversacion=conv, leido_por_admin=False).exclude(
        emisor=request.user
    ).update(leido_por_admin=True)

    mensajes = list(conv.mensajes.select_related("emisor").all())
    return render(
        request,
        "panel/mensajes_detalle.html",
        {"conv": conv, "mensajes": mensajes, "is_admin": is_admin},
    )


@login_required(login_url="/accounts/login/")
@require_POST
def panel_mensajes_cerrar(request, pk):
    redir = _requiere_panel(request)
    if redir:
        return redir
    conv = get_object_or_404(Conversacion, pk=pk)
    is_admin = request.user.is_staff or getattr(request.user, "es_administrador_tienda", False)
    if not is_admin and conv.administrador_asignado_id != request.user.id:
        messages.error(request, "No tienes permiso.")
        return redirect("panel_mensajes")
    conv.estado = "cerrada"
    conv.save(update_fields=["estado"])
    log_event(
        request=request,
        usuario=request.user,
        accion="cambio_estado",
        modulo="chat",
        entidad="Conversacion",
        entidad_id=str(conv.pk),
        descripcion="Cerrar conversación",
    )
    messages.success(request, "Conversación cerrada.")
    return redirect("panel_mensajes_detalle", pk=conv.pk)


@login_required(login_url="/accounts/login/")
@require_POST
def panel_mensajes_asignar(request, pk):
    redir = _requiere_panel(request)
    if redir:
        return redir
    conv = get_object_or_404(Conversacion, pk=pk)
    is_admin = request.user.is_staff or getattr(request.user, "es_administrador_tienda", False)
    if not is_admin:
        messages.error(request, "Solo admin puede asignar conversaciones.")
        return redirect("panel_mensajes_detalle", pk=conv.pk)
    quien = (request.POST.get("quien") or "").strip()
    if quien == "yo":
        conv.administrador_asignado = request.user
    elif quien == "nadie":
        conv.administrador_asignado = None
    conv.save(update_fields=["administrador_asignado"])
    log_event(
        request=request,
        usuario=request.user,
        accion="editar",
        modulo="chat",
        entidad="Conversacion",
        entidad_id=str(conv.pk),
        descripcion="Asignar conversación",
    )
    return redirect("panel_mensajes_detalle", pk=conv.pk)


@login_required(login_url="/accounts/login/")
def panel_ventas(request):
    """
    Ventas y clientes dentro del panel.
    Vista operativa de lectura/supervisión (no es checkout del cliente).
    """
    redir = _requiere_panel(request)
    if redir:
        return redir

    incluir_sim = (request.GET.get("sim") or "").strip() in ("1", "true", "yes", "on")
    q = (request.GET.get("q") or "").strip()
    estado = (request.GET.get("estado") or "").strip().lower()

    qv = Venta.objects.select_related("cliente")
    if not incluir_sim:
        qv = qv.filter(es_simulacion=False)
    if estado and estado in dict(Venta.ESTADOS_PEDIDO):
        qv = qv.filter(estado=estado)
    if q:
        q_id = int(q) if q.isdigit() else None
        qf = (
            Q(cliente__nombre__icontains=q)
            | Q(cliente__rut__icontains=q)
            | Q(cliente__email__icontains=q)
        )
        if q_id is not None:
            qf = qf | Q(id=q_id)
        qv = qv.filter(qf)

    ventas = (
        qv.prefetch_related("detalles__variante__producto").order_by("-fecha")[:100]
    )
    return render(
        request,
        "ventas.html",
        {
            "ventas": ventas,
            "incluir_simulaciones": incluir_sim,
            "filtros": {"q": q, "estado": estado},
            "estados": Venta.ESTADOS_PEDIDO,
        },
    )

@login_required(login_url="/accounts/login/")
def producto_listar(request):
    redir = _requiere_panel(request)
    if redir:
        return redir
    productos = Producto.objects.select_related("categoria").order_by(
        "-publicado", "categoria__nombre", "nombre"
    )
    stats = {
        "total": productos.count(),
        "publicados": productos.filter(publicado=True).count(),
        "ocultos": productos.filter(publicado=False).count(),
    }
    return render(
        request,
        "panel/producto_list.html",
        {"productos": productos, "stats": stats},
    )


@login_required(login_url="/accounts/login/")
@require_http_methods(["GET", "POST"])
def producto_nuevo(request):
    redir = _requiere_panel(request)
    if redir:
        return redir
    if request.method == "POST":
        form = ProductoPanelForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            log_event(
                request=request,
                usuario=request.user,
                accion="crear",
                modulo="catalogo",
                entidad="Producto",
                entidad_id=str(form.instance.pk),
                descripcion=f"Crear producto: {form.instance.nombre}",
            )
            messages.success(request, "Producto creado. Puedes añadir variantes abajo.")
            return redirect("panel_producto_editar", pk=form.instance.pk)
    else:
        form = ProductoPanelForm()
    return render(
        request,
        "panel/producto_form.html",
        {
            "form": form,
            "titulo": "Nuevo producto",
            "variante_formset": None,
            "producto": None,
            "preview_imagen_inicial": "",
        },
    )


@login_required(login_url="/accounts/login/")
@require_http_methods(["GET", "POST"])
def producto_editar(request, pk):
    redir = _requiere_panel(request)
    if redir:
        return redir
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == "POST":
        form = ProductoPanelForm(request.POST, request.FILES, instance=producto)
        formset = VarianteFormSet(request.POST, instance=producto)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            log_event(
                request=request,
                usuario=request.user,
                accion="editar",
                modulo="catalogo",
                entidad="Producto",
                entidad_id=str(producto.pk),
                descripcion=f"Editar producto: {producto.nombre}",
            )
            messages.success(request, "Cambios guardados.")
            return redirect("panel_producto_editar", pk=producto.pk)
    else:
        form = ProductoPanelForm(instance=producto)
        formset = VarianteFormSet(instance=producto)
    preview_imagen_inicial = producto.url_imagen_para_catalogo(request)
    return render(
        request,
        "panel/producto_form.html",
        {
            "form": form,
            "titulo": "Editar producto",
            "variante_formset": formset,
            "producto": producto,
            "preview_imagen_inicial": preview_imagen_inicial,
        },
    )


@login_required(login_url="/accounts/login/")
@require_http_methods(["GET", "POST"])
def producto_eliminar(request, pk):
    redir = _requiere_panel(request)
    if redir:
        return redir
    producto = get_object_or_404(Producto, pk=pk)
    if request.method == "POST":
        log_event(
            request=request,
            usuario=request.user,
            accion="eliminar",
            modulo="catalogo",
            entidad="Producto",
            entidad_id=str(producto.pk),
            descripcion=f"Eliminar producto: {producto.nombre}",
        )
        producto.delete()
        messages.success(request, "Producto eliminado.")
        return redirect("panel_productos")
    return render(request, "panel/producto_eliminar.html", {"producto": producto})


@login_required(login_url="/accounts/login/")
@require_POST
def producto_toggle_publicado(request, pk):
    redir = _requiere_panel(request)
    if redir:
        return redir
    producto = get_object_or_404(Producto, pk=pk)
    producto.publicado = not producto.publicado
    producto.save(update_fields=["publicado"])
    estado = "visible en catálogo" if producto.publicado else "oculto"
    log_event(
        request=request,
        usuario=request.user,
        accion="cambio_estado",
        modulo="catalogo",
        entidad="Producto",
        entidad_id=str(producto.pk),
        descripcion=f"Cambiar publicado: {producto.nombre} → {estado}",
    )
    messages.info(request, f"Producto {estado}.")
    return redirect("panel_productos")


@login_required(login_url="/accounts/login/")
def categoria_listar(request):
    redir = _requiere_panel(request)
    if redir:
        return redir
    categorias = Categoria.objects.order_by("nombre")
    stats = {"total": categorias.count()}
    return render(
        request,
        "panel/categoria_list.html",
        {"categorias": categorias, "stats": stats},
    )


def _categoria_form(request, categoria):
    redir = _requiere_panel(request)
    if redir:
        return redir
    if request.method == "POST":
        form = CategoriaPanelForm(request.POST, instance=categoria)
        if form.is_valid():
            form.save()
            log_event(
                request=request,
                usuario=request.user,
                accion="editar" if categoria else "crear",
                modulo="catalogo",
                entidad="Categoria",
                entidad_id=str(form.instance.pk),
                descripcion=f"{'Editar' if categoria else 'Crear'} categoría: {form.instance.nombre}",
            )
            messages.success(request, "Categoría guardada.")
            return redirect("panel_categorias")
    else:
        form = CategoriaPanelForm(instance=categoria)
    return render(
        request,
        "panel/categoria_form.html",
        {
            "form": form,
            "categoria": categoria,
            "titulo": "Editar categoría" if categoria else "Nueva categoría",
        },
    )


@login_required(login_url="/accounts/login/")
@require_http_methods(["GET", "POST"])
def categoria_nueva(request):
    return _categoria_form(request, None)


@login_required(login_url="/accounts/login/")
@require_http_methods(["GET", "POST"])
def categoria_editar(request, pk):
    cat = get_object_or_404(Categoria, pk=pk)
    return _categoria_form(request, cat)


@login_required(login_url="/accounts/login/")
@require_http_methods(["GET", "POST"])
def categoria_eliminar(request, pk):
    redir = _requiere_panel(request)
    if redir:
        return redir
    categoria = get_object_or_404(Categoria, pk=pk)
    if request.method == "POST":
        try:
            log_event(
                request=request,
                usuario=request.user,
                accion="eliminar",
                modulo="catalogo",
                entidad="Categoria",
                entidad_id=str(categoria.pk),
                descripcion=f"Eliminar categoría: {categoria.nombre}",
            )
            categoria.delete()
            messages.success(request, "Categoría eliminada.")
        except ProtectedError:
            messages.error(
                request,
                "No se puede eliminar: hay productos asociados a esta categoría.",
            )
        return redirect("panel_categorias")
    return render(request, "panel/categoria_eliminar.html", {"categoria": categoria})
