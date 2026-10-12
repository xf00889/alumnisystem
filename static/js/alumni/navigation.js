/* Alumni navigation is shared across breakpoints. Bootstrap manages the More menu and drawer. */
(() => {
  'use strict';
  function init() {
    const drawer = document.getElementById('alumniMobileMore');
    if (!drawer) return;
    // Leave navigation and focus handling to Bootstrap's built-in offcanvas behavior.
    // Prevent a stale opened drawer from surviving a transition to the desktop layout.
    const media = window.matchMedia('(min-width: 992px)');
    const closeOnDesktop = () => {
      if (media.matches && window.bootstrap && window.bootstrap.Offcanvas) {
        const instance = window.bootstrap.Offcanvas.getInstance(drawer);
        if (instance) instance.hide();
      }
    };
    if (media.addEventListener) media.addEventListener('change', closeOnDesktop);
    else if (media.addListener) media.addListener(closeOnDesktop);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
