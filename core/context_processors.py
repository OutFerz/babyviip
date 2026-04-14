"""Contexto global para plantillas públicas (configuración Babyviip)."""

import re


def _telefono_href(telefono: str) -> str:
    t = (telefono or "").strip()
    # deja solo dígitos, y si viene con +, lo mantenemos fuera (tel: requiere + opcional)
    digits = re.sub(r"\D+", "", t)
    if t.startswith("+"):
        return f"+{digits}"
    return digits


def contacto(_request):
    """
    Entrega configuración de contacto/redes/local.
    Se almacena en BD para permitir cambios sin editar HTML.
    """
    try:
        from erp.models import ConfiguracionSitio

        cfg = ConfiguracionSitio.objects.order_by("id").first()
        if cfg is None:
            cfg = ConfiguracionSitio.objects.create()
    except Exception:
        cfg = None

    if cfg is None:
        return {
            "contacto": {
                "nombre_tienda": "Babyviip",
                "instagram_usuario": "@babyviipcl",
                "instagram_url": "https://www.instagram.com/babyviipcl/",
                "facebook_nombre": "Grupo / página Babyviip",
                "facebook_url": "https://www.facebook.com/groups/1362338867173654/user/61587245798428/",
                "telefono": "+56 927493733",
                "telefono_href": "+56927493733",
                "correo": "babyviip8@gmail.com",
                "direccion": "Gran Avenida 5234, local 17, San Miguel",
                "mapa_url": "https://share.google/C6HMTq54TXQDafIMq",
                "whatsapp_url": "https://wa.me/56927493733",
                "texto_bienvenida": "Ropa y accesorios para bebés desde recién nacidos hasta 3 años.",
            }
        }

    return {
        "contacto": {
            "nombre_tienda": cfg.nombre_tienda,
            "instagram_usuario": cfg.instagram_usuario,
            "instagram_url": cfg.instagram_url,
            "facebook_nombre": cfg.facebook_nombre,
            "facebook_url": cfg.facebook_url,
            "telefono": cfg.telefono,
            "telefono_href": _telefono_href(cfg.telefono),
            "correo": cfg.correo,
            "direccion": cfg.direccion,
            "mapa_url": cfg.mapa_url,
            "whatsapp_url": cfg.whatsapp_url,
            "texto_bienvenida": cfg.texto_bienvenida,
        }
    }
