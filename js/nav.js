/**
 * Delad navigeringslogik — hamburgarmeny för responsiv layout.
 */
document.addEventListener('DOMContentLoaded', () => {
  const toggle = document.querySelector('.nav-toggle');
  if (!toggle) return;

  toggle.addEventListener('click', () => {
    const links = document.querySelector('.nav-links');
    const expanded = toggle.getAttribute('aria-expanded') === 'true';
    links.classList.toggle('open');
    toggle.setAttribute('aria-expanded', String(!expanded));
  });
});
