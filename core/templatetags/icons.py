"""SVG icon template tag."""
from __future__ import annotations

from django import template
from django.utils.html import format_html

register = template.Library()


_ICON_MAP: dict[str, str] = {
    "home": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
    'role="img" aria-hidden="true" fill="none" stroke="currentColor" '
    'stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" '
    'style="width:{size}px;height:{size}px;">'
    '<path d="M3.75 10.5 12 3.75 20.25 10.5" />'
    '<path d="M5.25 9.75V20.25H9.75V14.25H14.25V20.25H18.75V9.75" />'
    '</svg>',
    "car": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
    'role="img" aria-hidden="true" fill="none" stroke="currentColor" '
    'stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" '
    'style="width:{size}px;height:{size}px;">'
    '<path d="M4 16.5h16l-1-5.5a3 3 0 0 0-3-2.5H8a3 3 0 0 0-3 2.5z" />'
    '<path d="M6.5 16.5V18a1.5 1.5 0 0 1-3 0V15" />'
    '<path d="M17.5 16.5V18a1.5 1.5 0 0 0 3 0V15" />'
    '<path d="M8.5 16.5h7" />'
    '</svg>',
    "gas": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
    'role="img" aria-hidden="true" fill="none" stroke="currentColor" '
    'stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" '
    'style="width:{size}px;height:{size}px;">'
    '<path d="M5.5 4.5h7a1.5 1.5 0 0 1 1.5 1.5v13.5h-10V6a1.5 1.5 0 0 1 1.5-1.5z" />'
    '<path d="M8.5 2.5v2" />'
    '<path d="M17 6.5l2 2a1.5 1.5 0 0 1 .5 1.1V18a1.5 1.5 0 0 1-3 0v-3" />'
    '<path d="M6.5 11.5h5" />'
    '</svg>',
    "chart": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
    'role="img" aria-hidden="true" fill="none" stroke="currentColor" '
    'stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" '
    'style="width:{size}px;height:{size}px;">'
    '<path d="M4.5 19.5h15" />'
    '<path d="M7.5 16.5v-6" />'
    '<path d="M12 16.5v-9" />'
    '<path d="M16.5 16.5v-4" />'
    '</svg>',
    "cog": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
    'role="img" aria-hidden="true" fill="none" stroke="currentColor" '
    'stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" '
    'style="width:{size}px;height:{size}px;">'
    '<path d="M12 15.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7z" />'
    '<path d="M4.75 12a7.25 7.25 0 0 1 .08-1l-1.83-1.4 1.5-2.6 2.22.55a7.27 7.27 0 0 1 1.72-.99L8.74 3h3.02l.3 2.56c.6.2 1.19.49 1.72.85l2.33-.59 1.5 2.6-1.92 1.47c.06.33.1.66.1 1s-.04.67-.1 1l1.92 1.47-1.5 2.6-2.33-.59a7.3 7.3 0 0 1-1.72.85L11.76 21H8.74l-.3-2.56a7.27 7.27 0 0 1-1.72-.99l-2.22.55-1.5-2.6 1.83-1.4a7.25 7.25 0 0 1-.08-1z" />'
    '</svg>',
    "plus": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
    'role="img" aria-hidden="true" fill="none" stroke="currentColor" '
    'stroke-width="1.8" stroke-linecap="round" '
    'style="width:{size}px;height:{size}px;">'
    '<path d="M12 5v14" />'
    '<path d="M5 12h14" />'
    '</svg>',
    "edit": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
    'role="img" aria-hidden="true" fill="none" stroke="currentColor" '
    'stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" '
    'style="width:{size}px;height:{size}px;">'
    '<path d="M5 15.5V19h3.5l9.9-9.9a2.47 2.47 0 0 0-3.5-3.5z" />'
    '<path d="M13.5 7.5l3 3" />'
    '</svg>',
    "trash": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
    'role="img" aria-hidden="true" fill="none" stroke="currentColor" '
    'stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" '
    'style="width:{size}px;height:{size}px;">'
    '<path d="M5.5 7.5h13" />'
    '<path d="M9 5.5h6" />'
    '<path d="M9.75 10.5v7" />'
    '<path d="M14.25 10.5v7" />'
    '<path d="M7.5 7.5V19a1.5 1.5 0 0 0 1.5 1.5h6a1.5 1.5 0 0 0 1.5-1.5V7.5" />'
    '</svg>',
    "alert": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
    'role="img" aria-hidden="true" fill="none" stroke="currentColor" '
    'stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" '
    'style="width:{size}px;height:{size}px;">'
    '<path d="M12 4.5 3.5 19.5h17z" />'
    '<path d="M12 10v4.5" />'
    '<path d="M12 17.5h.01" />'
    '</svg>',
    "user": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
    'role="img" aria-hidden="true" fill="none" stroke="currentColor" '
    'stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" '
    'style="width:{size}px;height:{size}px;">'
    '<path d="M12 12.5a4 4 0 1 0-4-4 4 4 0 0 0 4 4z" />'
    '<path d="M5 19.5a7 7 0 0 1 14 0" />'
    '</svg>',
    "logout": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
    'role="img" aria-hidden="true" fill="none" stroke="currentColor" '
    'stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" '
    'style="width:{size}px;height:{size}px;">'
    '<path d="M15.5 5.5v-1a1.5 1.5 0 0 0-1.5-1.5H6A1.5 1.5 0 0 0 4.5 4.5v15A1.5 1.5 0 0 0 6 21h8a1.5 1.5 0 0 0 1.5-1.5v-1" />'
    '<path d="M10.5 12h9" />'
    '<path d="m16.5 8.5 3.5 3.5-3.5 3.5" />'
    '</svg>',
}


def _normalize_size(size: object) -> int:
    try:
        size_value = int(size)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 20
    return size_value if size_value > 0 else 20


@register.simple_tag
def icon(name: str, size: object = 20, cls: str | None = None) -> str:
    """Render an inline SVG icon.

    Unknown icon names fall back to a harmless span so templates never crash.
    """

    icon_name = (name or "").strip().lower()
    classes = "icon"
    extra_cls = (cls or "").strip()
    if extra_cls:
        classes = f"{classes} {extra_cls}"

    size_value = _normalize_size(size)
    svg_template = _ICON_MAP.get(icon_name)
    if not svg_template:
        return format_html('<span class="{} icon-missing" aria-hidden="true"></span>', classes)

    svg_markup = format_html(svg_template, size=size_value)
    return format_html('<span class="{}" aria-hidden="true">{}</span>', classes, svg_markup)
