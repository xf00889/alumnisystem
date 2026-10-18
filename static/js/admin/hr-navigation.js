/* HR workspace compact navigation, without altering desktop links or forms. */
(() => {
  'use strict';
  const header = document.querySelector('body.hr-workspace .hr-topbar');
  if (!header) return;
  const nav = header.querySelector('#hr-primary-nav');
  const toggle = header.querySelector('.hr-nav-toggle');
  const backdrop = document.querySelector('.hr-nav-backdrop');
  if (!nav || !toggle) return;
  const mobileQuery = window.matchMedia('(max-width: 900px)');
  function setOpen(open, restoreFocus = false) {
    const expanded = Boolean(open && mobileQuery.matches);
    const wasOpen = header.classList.contains('hr-menu-open');
    header.classList.toggle('hr-menu-open', expanded);
    document.body.classList.toggle('hr-nav-open', expanded);
    toggle.setAttribute('aria-expanded', String(expanded));
    toggle.setAttribute('aria-label', expanded ? 'Close HR navigation' : 'Open HR navigation');
    const menuIcon = toggle.querySelector('i');
    if (menuIcon) { menuIcon.classList.toggle('fa-bars', !expanded); menuIcon.classList.toggle('fa-xmark', expanded); }
    if (backdrop) backdrop.hidden = !expanded;
    if (wasOpen && !expanded && restoreFocus) toggle.focus();
  }
  toggle.addEventListener('click', () => setOpen(!header.classList.contains('hr-menu-open')));
  if (backdrop) backdrop.addEventListener('click', () => setOpen(false, true));
  nav.querySelectorAll('a[href]').forEach(link => {
    link.addEventListener('click', () => { if (mobileQuery.matches) setOpen(false); });
  });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && header.classList.contains('hr-menu-open')) {
      setOpen(false, true);
      event.preventDefault();
    }
  });
  document.addEventListener('pointerdown', event => {
    if (header.classList.contains('hr-menu-open') && !header.contains(event.target)) setOpen(false);
  });
  if (mobileQuery.addEventListener) mobileQuery.addEventListener('change', () => setOpen(false));
  else window.addEventListener('resize', () => { if (!mobileQuery.matches) setOpen(false); });
})();
