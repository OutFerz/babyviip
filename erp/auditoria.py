import ipaddress

from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver


def _client_ip(request):
    if request is None:
        return None
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        cand = (xff.split(",")[0] or "").strip()
    else:
        cand = (request.META.get("REMOTE_ADDR") or "").strip()
    if not cand:
        return None
    try:
        ipaddress.ip_address(cand)
        return cand
    except ValueError:
        return None


def _user_agent(request):
    if request is None:
        return ""
    return (request.META.get("HTTP_USER_AGENT") or "").strip()[:400]


def _rol(user):
    if user is None or not getattr(user, "is_authenticated", False):
        return ""
    if getattr(user, "is_superuser", False):
        return "superuser"
    if getattr(user, "is_staff", False):
        return "staff"
    if getattr(user, "es_administrador_tienda", False):
        return "admin_tienda"
    if getattr(user, "es_empleado", False):
        return "empleado"
    return "usuario"


def log_event(
    *,
    request=None,
    usuario=None,
    accion: str,
    modulo: str = "",
    entidad: str = "",
    entidad_id: str = "",
    descripcion: str = "",
):
    """
    Registro de auditoría (best-effort).
    Nunca debe romper una acción del sistema si falla el guardado.
    """
    try:
        from .models import Auditoria

        Auditoria.objects.create(
            usuario=usuario,
            rol=_rol(usuario),
            accion=accion,
            modulo=(modulo or "")[:100],
            entidad=(entidad or "")[:100],
            entidad_id=(entidad_id or "")[:50],
            descripcion=(descripcion or "")[:2000],
            ip=_client_ip(request),
            user_agent=_user_agent(request),
        )
    except Exception:
        return


@receiver(user_logged_in)
def _audit_login(sender, request, user, **kwargs):
    log_event(
        request=request,
        usuario=user,
        accion="login",
        modulo="auth",
        entidad="Usuario",
        entidad_id=str(getattr(user, "pk", "") or ""),
        descripcion="Inicio de sesión",
    )


@receiver(user_logged_out)
def _audit_logout(sender, request, user, **kwargs):
    log_event(
        request=request,
        usuario=user,
        accion="logout",
        modulo="auth",
        entidad="Usuario",
        entidad_id=str(getattr(user, "pk", "") or ""),
        descripcion="Cierre de sesión",
    )

