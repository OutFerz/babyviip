from django import template

register = template.Library()


@register.filter
def get_item(d, key):
    if d is None:
        return None
    try:
        return d.get(key)
    except Exception:
        try:
            return d[key]
        except Exception:
            return None

