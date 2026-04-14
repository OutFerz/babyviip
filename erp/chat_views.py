from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from .auditoria import log_event
from .models import Conversacion, Mensaje


def _puede_usar_chat_cliente(user):
    return user.is_authenticated and getattr(user, "es_cliente", False)


@login_required(login_url="/accounts/login/")
def mis_conversaciones(request):
    if not _puede_usar_chat_cliente(request.user):
        messages.warning(request, "Este módulo es para clientes.")
        return redirect("home")

    convs = (
        Conversacion.objects.filter(cliente=request.user)
        .annotate(
            no_leidos=Count(
                "mensajes",
                filter=Q(mensajes__leido_por_cliente=False)
                & ~Q(mensajes__emisor=request.user),
            )
        )
        .order_by("-actualizada_en")
    )
    return render(request, "chat/mis_conversaciones.html", {"convs": convs})


@login_required(login_url="/accounts/login/")
@require_http_methods(["GET", "POST"])
def conversacion_nueva(request):
    if not _puede_usar_chat_cliente(request.user):
        messages.warning(request, "Este módulo es para clientes.")
        return redirect("home")

    if request.method == "POST":
        asunto = (request.POST.get("asunto") or "").strip()[:120]
        contenido = (request.POST.get("contenido") or "").strip()
        if len(contenido) < 2:
            messages.error(request, "Escribe tu consulta (mínimo 2 caracteres).")
            return redirect("conversacion_nueva")

        with transaction.atomic():
            conv = Conversacion.objects.create(cliente=request.user, asunto=asunto)
            Mensaje.objects.create(
                conversacion=conv,
                emisor=request.user,
                contenido=contenido,
                leido_por_cliente=True,
                leido_por_admin=False,
            )

        log_event(
            request=request,
            usuario=request.user,
            accion="crear",
            modulo="chat",
            entidad="Conversacion",
            entidad_id=str(conv.pk),
            descripcion="Cliente crea conversación",
        )
        log_event(
            request=request,
            usuario=request.user,
            accion="crear",
            modulo="chat",
            entidad="Mensaje",
            entidad_id=str(conv.pk),
            descripcion="Cliente envía mensaje",
        )
        messages.success(request, "Mensaje enviado. Te responderemos pronto.")
        return redirect("conversacion_detalle", pk=conv.pk)

    return render(request, "chat/conversacion_nueva.html")


@login_required(login_url="/accounts/login/")
@require_http_methods(["GET", "POST"])
def conversacion_detalle(request, pk):
    if not _puede_usar_chat_cliente(request.user):
        messages.warning(request, "Este módulo es para clientes.")
        return redirect("home")

    conv = get_object_or_404(Conversacion, pk=pk, cliente=request.user)

    if request.method == "POST":
        if conv.estado != "abierta":
            messages.error(request, "La conversación está cerrada.")
            return redirect("conversacion_detalle", pk=conv.pk)
        contenido = (request.POST.get("contenido") or "").strip()
        if len(contenido) < 1:
            messages.error(request, "Mensaje vacío.")
            return redirect("conversacion_detalle", pk=conv.pk)
        Mensaje.objects.create(
            conversacion=conv,
            emisor=request.user,
            contenido=contenido,
            leido_por_cliente=True,
            leido_por_admin=False,
        )
        log_event(
            request=request,
            usuario=request.user,
            accion="crear",
            modulo="chat",
            entidad="Mensaje",
            entidad_id=str(conv.pk),
            descripcion="Cliente envía mensaje",
        )
        return redirect("conversacion_detalle", pk=conv.pk)

    # Marcar como leído por cliente los mensajes de admin
    Mensaje.objects.filter(
        conversacion=conv, leido_por_cliente=False
    ).exclude(emisor=request.user).update(leido_por_cliente=True)

    mensajes = list(conv.mensajes.select_related("emisor").all())
    return render(
        request,
        "chat/conversacion_detalle.html",
        {"conv": conv, "mensajes": mensajes},
    )

