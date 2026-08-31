from pathlib import Path
import re

CONTACT_URL = 'https://www.instagram.com/desarrollamoficial'

NAV_ITEMS = (
    '<a href="/">Inicio</a>'
    '<a href="/servicios">Servicios</a>'
    '<a href="/galeria">Galería</a>'
    '<a href="/manifiesto">Manifiesto</a>'
    '<a href="/inversiones">Inversiones</a>'
)


def active_nav(page: str) -> str:
    html = NAV_ITEMS
    current = {
        'servicios.html': '/servicios',
        'galeria.html': '/galeria',
        'inversiones.html': '/inversiones',
    }.get(page)
    if current:
        html = html.replace(
            f'<a href="{current}">',
            f'<a href="{current}" aria-current="page" class="is-active">',
            1,
        )
    return html


def mobile_nav(page: str) -> str:
    html = NAV_ITEMS
    current = {
        'servicios.html': '/servicios',
        'galeria.html': '/galeria',
        'inversiones.html': '/inversiones',
    }.get(page)
    if current:
        html = html.replace(
            f'<a href="{current}">',
            f'<a href="{current}" aria-current="page">',
            1,
        )
    return html


def patch(path: Path) -> None:
    text = path.read_text(encoding='utf-8')
    page = path.name

    desktop = (
        '<nav class="amo-nav" aria-label="Navegación principal">'
        + active_nav(page)
        + '</nav>'
    )
    text, n_desktop = re.subn(
        r'<nav class="amo-nav"(?: aria-label="Navegación principal")?>.*?</nav>',
        desktop,
        text,
        count=1,
        flags=re.S,
    )
    if n_desktop != 1:
        raise SystemExit(f'{page}: no se encontró navegación desktop única')

    contact = (
        f'<a class="amo-contact" href="{CONTACT_URL}" target="_blank" '
        'rel="noopener noreferrer">Hablemos</a>'
    )
    text, n_contact = re.subn(
        r'<a class="amo-contact"[^>]*>.*?</a>',
        contact,
        text,
        count=1,
        flags=re.S,
    )
    if n_contact != 1:
        raise SystemExit(f'{page}: no se encontró contacto único')

    details = (
        '<details class="amo-menu"><summary>Menú</summary>'
        '<nav class="amo-menu__panel" aria-label="Navegación móvil">'
        + mobile_nav(page)
        + '</nav></details>'
    )
    if '<details class="amo-menu">' in text:
        text, n_mobile = re.subn(
            r'<details class="amo-menu">.*?</details>',
            details,
            text,
            count=1,
            flags=re.S,
        )
        if n_mobile != 1:
            raise SystemExit(f'{page}: menú móvil ambiguo')
    else:
        marker = contact
        text = text.replace(marker, marker + details, 1)

    assert text.count('href="/inversiones"') >= 2
    assert text.count('class="amo-menu"') == 1
    path.write_text(text, encoding='utf-8')
    print(f'OK: {page}')


for filename in ('servicios.html', 'galeria.html', 'inversiones.html'):
    patch(Path(filename))
