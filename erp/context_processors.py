from django.db.models import Q


def panel_unread_counts(request):
    """
    Contadores globales para el panel (p.ej. badge de Mensajes).
    Se mantiene liviano: una sola query COUNT si aplica.
    """
    user = getattr(request, "user", None)
    if not user or not getattr(user, "is_authenticated", False):
        return {"panel_counts": {"mensajes_no_leidos": 0}}

    puede_panel = user.is_staff or getattr(user, "es_administrador_tienda", False) or getattr(
        user, "es_empleado", False
    )
    if not puede_panel:
        return {"panel_counts": {"mensajes_no_leidos": 0}}

    try:
        from .models import Mensaje

        # No leído por admin: mensajes donde el emisor NO es el usuario actual,
        # que aún no están marcados como leídos por admin, y conversación abierta.
        n = (
            Mensaje.objects.filter(
                leido_por_admin=False,
                conversacion__estado="abierta",
            )
            .exclude(emisor=user)
            .count()
        )
        return {"panel_counts": {"mensajes_no_leidos": int(n)}}
    except Exception:
        return {"panel_counts": {"mensajes_no_leidos": 0}}

