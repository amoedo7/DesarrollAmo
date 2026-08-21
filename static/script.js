document.addEventListener('DOMContentLoaded', () => {
  const htmlEl = document.documentElement;
  const toggleBtn = document.getElementById('darkToggle');

  // Modo oscuro: algunas páginas no tienen botón. Nunca debe romper el resto del JS.
  function setDarkMode(dark) {
    htmlEl.classList.toggle('dark', Boolean(dark));
    if (toggleBtn) toggleBtn.textContent = dark ? '☀️' : '🌙';
    try {
      localStorage.setItem('darkMode', dark ? 'true' : 'false');
    } catch (_) {
      // La UI debe seguir funcionando aunque storage esté bloqueado.
    }
  }

  let savedMode = null;
  try {
    savedMode = localStorage.getItem('darkMode');
  } catch (_) {}

  const prefersDark = window.matchMedia?.('(prefers-color-scheme: dark)').matches ?? false;
  setDarkMode(savedMode === null ? prefersDark : savedMode === 'true');

  if (toggleBtn) {
    toggleBtn.addEventListener('click', () => {
      setDarkMode(!htmlEl.classList.contains('dark'));
    });
  }

  // Reveal progresivo. Si IntersectionObserver no existe, mostrar todo inmediatamente.
  const fadeInElements = document.querySelectorAll('.fade-in');
  if ('IntersectionObserver' in window) {
    const fadeInObserver = new IntersectionObserver((entries, observer) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          observer.unobserve(entry.target);
        }
      });
    }, { root: null, rootMargin: '0px', threshold: 0.15 });

    fadeInElements.forEach(el => fadeInObserver.observe(el));
  } else {
    fadeInElements.forEach(el => el.classList.add('visible'));
  }

  // Toggle Galería
  const btn = document.getElementById('toggleGallery');
  const gallery = document.getElementById('gallerySection');

  if (btn && gallery) {
    btn.addEventListener('click', () => {
      const isShown = gallery.classList.toggle('show');
      gallery.setAttribute('aria-hidden', String(!isShown));
      btn.textContent = isShown ? 'Ocultar Galería' : 'Mostrar Galería';
    });
  }

  // Scroll suave para navegación interna
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      const href = this.getAttribute('href');
      if (!href || href === '#') return;
      const target = document.querySelector(href);
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth' });
      }
    });
  });

  console.log('Script DesarrollAMO cargado correctamente');
});
