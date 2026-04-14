"""
API ligera para el catálogo público: favoritos (⭐) y registro de búsquedas.
Llamada desde: static/js/catalogo.js · URLs: core/urls.py
"""

import ipaddress
import json

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST

from .models import Busqueda, Favorito, Producto


def _client_ip(request):
    """IP del cliente; respeta X-Forwarded-For si hay proxy. Inválida → None."""
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    raw = (xff.split(",")[0].strip() if xff else "") or (
        request.META.get("REMOTE_ADDR") or ""
    ).strip()
    if not raw:
        return None
    try:
        return str(ipaddress.ip_address(raw))
    except ValueError:
        return None


def _user_agent(request):
    ua = (request.META.get("HTTP_USER_AGENT") or "").strip()
    return ua[:2000] if ua else None


@require_POST
def favorito_toggle(request):
    """Alterna Favorito para el usuario autenticado. JSON: {\"producto_id\": <int>}."""
    if not request.user.is_authenticated:
        return JsonResponse({"detail": "Se requiere iniciar sesión."}, status=401)
    try:
        payload = json.loads(request.body.decode() or "{}")
        pid = int(payload.get("producto_id"))
    except (TypeError, ValueError, json.JSONDecodeError):
        return JsonResponse({"detail": "producto_id inválido."}, status=400)
    producto = get_object_or_404(Producto, pk=pid)
    existing = Favorito.objects.filter(usuario=request.user, producto=producto).first()
    if existing:
        existing.delete()
        return JsonResponse({"favorito": False})
    Favorito.objects.create(usuario=request.user, producto=producto)
    return JsonResponse({"favorito": True})


@require_POST
def busqueda_log(request):
    """Registra un término buscado (anon o usuario). POST form: termino=."""
    termino = (request.POST.get("termino") or "").strip()[:100]
    if len(termino) < 2:
        return JsonResponse({"ok": False})
    Busqueda.objects.create(
        termino=termino,
        usuario=request.user if request.user.is_authenticated else None,
        ip=_client_ip(request),
        user_agent=_user_agent(request),
    )
    return JsonResponse({"ok": True})
