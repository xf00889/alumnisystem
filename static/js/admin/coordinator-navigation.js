/* Coordinator navigation: one-row topbar with an accessible mobile menu. */
(() => {
  'use strict';
  const header = document.querySelector('.coordinator-topbar');
  if (!header) return;
  const nav = header.querySelector('#coordinator-primary-nav');
  const toggle = header.querySelector('.coordinator-nav-toggle');
  const backdrop = document.querySelector('.coordinator-nav-backdrop');
  if (!nav || !toggle) return;
  const mobileQuery = window.matchMedia('(max-width: 1220px)');
  const groups = Array.from(nav.querySelectorAll('.coordinator-menu-group'));

  function closeGroups(except = null) {
    groups.forEach(group => { if (group !== except) group.open = false; });
  }
  function setMobileOpen(open, restoreFocus = false) {
    const expanded = Boolean(open && mobileQuery.matches);
    const wasOpen = header.classList.contains('is-menu-open');
    header.classList.toggle('is-menu-open', expanded);
    document.body.classList.toggle('coordinator-nav-open', expanded);
    toggle.setAttribute('aria-expanded', String(expanded));
    toggle.setAttribute('aria-label', expanded ? 'Close coordinator navigation' : 'Open coordinator navigation');
    const menuIcon = toggle.querySelector('i');
    if (menuIcon) { menuIcon.classList.toggle('fa-bars', !expanded); menuIcon.classList.toggle('fa-xmark', expanded); }
    if (backdrop) backdrop.hidden = !expanded;
    if (!expanded) closeGroups();
    if (wasOpen && !expanded && restoreFocus) toggle.focus();
  }

  toggle.addEventListener('click', () => {
    setMobileOpen(!header.classList.contains('is-menu-open'));
  });
  if (backdrop) backdrop.addEventListener('click', () => setMobileOpen(false, true));

  groups.forEach(group => {
    group.addEventListener('toggle', () => {
      if (group.open) closeGroups(group);
    });
  });
  nav.querySelectorAll('a[href]').forEach(link => {
    link.addEventListener('click', () => { if (mobileQuery.matches) setMobileOpen(false); });
  });
  document.addEventListener('pointerdown', event => {
    if (header.contains(event.target)) {
      if (!nav.contains(event.target) && !toggle.contains(event.target)) closeGroups();
      return;
    }
    if (header.classList.contains('is-menu-open')) setMobileOpen(false);
    else closeGroups();
  });
  document.addEventListener('keydown', event => {
    if (event.key !== 'Escape') return;
    const group = groups.find(item => item.open);
    if (group) {
      closeGroups();
      group.querySelector('summary')?.focus();
      event.preventDefault();
    } else if (header.classList.contains('is-menu-open')) {
      setMobileOpen(false, true);
      event.preventDefault();
    }
  });
  if (mobileQuery.addEventListener) {
    mobileQuery.addEventListener('change', () => setMobileOpen(false));
  } else {
    window.addEventListener('resize', () => { if (!mobileQuery.matches) setMobileOpen(false); });
  }
})();
