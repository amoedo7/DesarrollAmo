from pathlib import Path
import re

CONTACT_URL = 'https://www.instagram.com/desarrollamoficial'

NAV_ITEMS = (
    '<a href="index.html">Inicio</a>'
    '<a href="servicios.html">Servicios</a>'
    '<a href="galeria.html">Galería</a>'
    '<a href="manifiesto.html">Manifiesto</a>'
    '<a href="inversiones.html">Inversiones</a>'
)

CURRENT = {
    'index.html': 'index.html',
    'servicios.html': 'servicios.html',
    'galeria.html': 'galeria.html',
    'manifiesto.html': 'manifiesto.html',
    'inversiones.html': 'inversiones.html',
}


def build_nav(page: str, mobile: bool = False) -> str:
    html = NAV_ITEMS
    current = CURRENT.get(page)
    if current:
        attrs = ' aria-current="page"' if mobile else ' aria-current="page" class="is-active"'
        html = html.replace(
            f'<a href="{current}">',
            f'<a href="{current}"{attrs}>',
            1,
        )
    return html


def patch(path: Path) -> None:
    text = path.read_text(encoding='utf-8')
    page = path.name

    desktop = (
        '<nav class="amo-nav" aria-label="Navegación principal">'
        + build_nav(page)
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
        + build_nav(page, mobile=True)
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
        text = text.replace(contact, contact + details, 1)

    for target in CURRENT.values():
        assert f'href="{target}"' in text
    assert text.count('class="amo-menu"') == 1
    path.write_text(text, encoding='utf-8')
    print(f'OK: {page}')


for filename in CURRENT:
    patch(Path(filename))
