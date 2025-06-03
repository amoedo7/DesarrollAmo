document.addEventListener('DOMContentLoaded', () => {
  // Toggle modo oscuro y guardado en localStorage
  const toggleBtn = document.getElementById('darkToggle');
  const htmlEl = document.documentElement;

  function setDarkMode(dark) {
    if (dark) {
      htmlEl.classList.add('dark');
      toggleBtn.textContent = '☀️';
    } else {
      htmlEl.classList.remove('dark');
      toggleBtn.textContent = '🌙';
    }
    localStorage.setItem('darkMode', dark ? 'true' : 'false');
  }

  const savedMode = localStorage.getItem('darkMode');
  if (savedMode === null) {
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    setDarkMode(prefersDark);
  } else {
    setDarkMode(savedMode === 'true');
  }

  toggleBtn.addEventListener('click', () => {
    const isDark = htmlEl.classList.contains('dark');
    setDarkMode(!isDark);
  });

  // Animación fade-in con IntersectionObserver
  const fadeInElements = document.querySelectorAll('.fade-in');

  const observerOptions = {
    root: null, // viewport
    rootMargin: '0px',
    threshold: 0.15, // 15% visible
  };

  const fadeInObserver = new IntersectionObserver((entries, observer) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        observer.unobserve(entry.target); // deja de observar para mejorar rendimiento
      }
    });
  }, observerOptions);

  fadeInElements.forEach(el => fadeInObserver.observe(el));

  // Toggle Galería
  const btn = document.getElementById('toggleGallery');
  const gallery = document.getElementById('gallerySection');

  if (btn && gallery) {
    btn.addEventListener('click', () => {
      const isShown = gallery.classList.toggle('show');
      gallery.setAttribute('aria-hidden', !isShown);
      btn.textContent = isShown ? 'Ocultar Galería' : 'Mostrar Galería';
    });
  }

  // Scroll suave para navegación interna
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      const target = document.querySelector(this.getAttribute('href'));
      if (target) {
        e.preventDefault();
        target.scrollIntoView({
          behavior: 'smooth'
        });
      }
    });
  });

  console.log("Script DAMO cargado correctamente");

  // Aquí puedes añadir futuros scripts para cargar audios/videos dinámicamente
});
