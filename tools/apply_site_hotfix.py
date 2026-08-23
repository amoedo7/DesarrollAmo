from pathlib import Path
import re

path = Path('servicios.html')
text = path.read_text(encoding='utf-8')

css_link = '  <link rel="stylesheet" href="/static/site-shell.css" />\n'
if '/static/site-shell.css' not in text:
    marker = '  <title>Servicios · DesarrollAMO</title>\n'
    if marker not in text:
        raise SystemExit('No se encontró el <title> esperado en servicios.html')
    text = text.replace(marker, marker + css_link, 1)

header = '''  <header class="amo-header">
    <div class="amo-header__inner">
      <a class="amo-brand" href="/" aria-label="DesarrollAMO inicio">desarroll<span>AMO</span></a>
      <nav class="amo-nav" aria-label="Navegación principal">
        <a href="/">Inicio</a><a href="/clientes">Clientes</a><a href="/manifiesto">Manifiesto</a><a href="/servicios" aria-current="page" class="is-active">Servicios</a><a href="/galeria">Galería</a>
      </nav>
      <a class="amo-contact" href="/#contacto">Hablemos</a>
      <details class="amo-menu"><summary>Menú</summary><nav class="amo-menu__panel" aria-label="Navegación móvil"><a href="/">Inicio</a><a href="/clientes">Clientes</a><a href="/manifiesto">Manifiesto</a><a href="/servicios" aria-current="page">Servicios</a><a href="/galeria">Galería</a></nav></details>
    </div>
  </header>'''

pattern_header = re.compile(r'\s*<header class="topbar">.*?</header>\s*<nav class="mobile-drawer".*?</nav>', re.S)
text, n_header = pattern_header.subn('\n' + header, text, count=1)
if n_header != 1:
    raise SystemExit(f'Header de Servicios no parcheado; coincidencias={n_header}')

footer = '''  <footer class="amo-footer">
    <div class="amo-footer__inner">
      <div class="amo-footer__brand"><a class="amo-brand" href="/">desarroll<span>AMO</span></a><p>Tecnología, diseño y automatización construidos alrededor de problemas reales.</p></div>
      <nav class="amo-footer__links" aria-label="Navegación de pie"><a href="/">Inicio</a><a href="/clientes">Clientes</a><a href="/manifiesto">Manifiesto</a><a href="/servicios">Servicios</a><a href="/galeria">Galería</a><a href="https://github.com/amoedo7" target="_blank" rel="noopener">GitHub</a></nav>
    </div>
    <div class="amo-footer__bottom"><span>© 2026 DesarrollAMO</span><span>Construimos · probamos · publicamos</span></div>
  </footer>'''

pattern_footer = re.compile(r'\s*<footer class="footer">.*?</footer>\s*</div>\s*(<script>)', re.S)
text, n_footer = pattern_footer.subn('\n  </div>\n' + footer + '\n  \\1', text, count=1)
if n_footer != 1:
    raise SystemExit(f'Footer de Servicios no parcheado; coincidencias={n_footer}')

assert '<header class="topbar">' not in text
assert '<footer class="footer">' not in text
assert text.count('class="amo-header"') == 1
assert text.count('class="amo-footer"') == 1
assert '/static/site-shell.css' in text

path.write_text(text, encoding='utf-8')
print('OK: Servicios usa shell global namespaced; contenido interno preservado.')
