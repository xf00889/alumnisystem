/* Progressive enhancement for native <details> dropdowns and the coordinator mobile menu. */
(() => {
  'use strict';
  const header = document.querySelector('.coordinator-topbar');
  if (!header) return;
  const nav = header.querySelector('#coordinator-primary-nav');
  const toggle = header.querySelector('.coordinator-nav-toggle');
  if (!nav || !toggle) return;
  const groups = Array.from(nav.querySelectorAll('.coordinator-menu-group'));

  function closeGroups(except) {
    groups.forEach((group) => { if (group !== except) group.open = false; });
  }
  function closeMobile(restoreFocus = false) {
    const wasOpen = header.classList.contains('is-menu-open');
    header.classList.remove('is-menu-open');
    toggle.setAttribute('aria-expanded', 'false');
    if (wasOpen && restoreFocus) toggle.focus();
  }
  toggle.addEventListener('click', () => {
    const willOpen = !header.classList.contains('is-menu-open');
    header.classList.toggle('is-menu-open', willOpen);
    toggle.setAttribute('aria-expanded', String(willOpen));
    if (!willOpen) closeGroups();
  });
  groups.forEach((group) => {
    group.addEventListener('toggle', () => {
      if (group.open) closeGroups(group);
    });
  });
  document.addEventListener('pointerdown', (event) => {
    if (header.contains(event.target)) {
      if (!nav.contains(event.target) && event.target !== toggle && !toggle.contains(event.target)) closeGroups();
      return;
    }
    closeGroups();
    closeMobile();
  });
  document.addEventListener('keydown', (event) => {
    if (event.key !== 'Escape') return;
    const openGroup = groups.find((group) => group.open);
    if (openGroup) {
      closeGroups();
      openGroup.querySelector('summary')?.focus();
      event.preventDefault();
    } else if (header.classList.contains('is-menu-open')) {
      closeMobile(true);
      event.preventDefault();
    }
  });
  window.addEventListener('resize', () => {
    if (window.innerWidth > 1220) closeMobile();
  });
})();
