(() => {
  'use strict';
  const cards = [...document.querySelectorAll('.project-card')];
  const filters = [...document.querySelectorAll('.gallery-filter')];
  const search = document.querySelector('#gallerySearch');
  const status = document.querySelector('#galleryStatus');
  const empty = document.querySelector('#galleryEmpty');
  if (!cards.length) return;

  const normalize = value => (value || '').toLocaleLowerCase('es').normalize('NFD').replace(/[\u0300-\u036f]/g, '');
  const showAll = () => cards.forEach(card => { card.hidden = false; });
  let activeFilter = 'all';

  function applyFilters() {
    try {
      const term = normalize(search?.value || '');
      let visible = 0;
      cards.forEach(card => {
        const cats = (card.dataset.category || '').split(/\s+/);
        const categoryMatch = activeFilter === 'all' || cats.includes(activeFilter);
        const textMatch = !term || normalize(card.textContent).includes(term);
        const show = categoryMatch && textMatch;
        card.hidden = !show;
        if (show) visible += 1;
      });
      if (status) status.textContent = `${visible} proyecto${visible === 1 ? '' : 's'} visible${visible === 1 ? '' : 's'}`;
      empty?.classList.toggle('is-visible', visible === 0);
    } catch (error) {
      console.error('Galería: se desactivaron los filtros para preservar el contenido.', error);
      showAll();
      if (status) status.textContent = `${cards.length} proyectos visibles`;
      empty?.classList.remove('is-visible');
    }
  }

  filters.forEach(button => button.addEventListener('click', () => {
    activeFilter = button.dataset.filter || 'all';
    filters.forEach(item => item.classList.toggle('is-active', item === button));
    applyFilters();
  }));
  search?.addEventListener('input', applyFilters);
  document.querySelectorAll('.project-visual img').forEach(img => img.addEventListener('error', () => img.classList.add('is-broken')));

  /* Cards are visible in HTML/CSS before this script runs. JS only narrows results. */
  applyFilters();
})();
