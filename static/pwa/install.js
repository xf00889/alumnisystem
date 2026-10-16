/* NORSU PWA installation and updates. No telemetry, server writes or push permission. */
(() => {
  'use strict';
  if (!window.isSecureContext || !('serviceWorker' in navigator)) return;
  let installPrompt = null;
  let awaitingReload = false;
  let modalReturnFocus = null;
  const isStandalone = () => window.matchMedia('(display-mode: standalone)').matches || navigator.standalone === true;
  const isiOS = /iphone|ipad|ipod/i.test(navigator.userAgent);
  const installButtons = [...document.querySelectorAll('[data-pwa-install]')];
  const updateButtons = [...document.querySelectorAll('[data-pwa-update]')];
  const help = document.getElementById('norsuPwaHelp');
  const helpPanel = help && help.querySelector('.norsu-pwa-help__panel');
  const setVisible = (controls, visible) => controls.forEach((control) => { control.hidden = !visible; });
  const showHelp = () => {
    if (!help) return;
    modalReturnFocus = document.activeElement;
    help.hidden = false;
    helpPanel.focus();
  };
  const closeHelp = () => {
    if (!help) return;
    help.hidden = true;
    if (modalReturnFocus && typeof modalReturnFocus.focus === 'function') modalReturnFocus.focus();
  };
  if (help) {
    help.querySelectorAll('[data-pwa-close]').forEach((element) => element.addEventListener('click', closeHelp));
    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape' && !help.hidden) closeHelp();
      if (event.key === 'Tab' && !help.hidden) {
        // This simple dialog has a single focusable action.
        event.preventDefault();
        help.querySelector('button[data-pwa-close]').focus();
      }
    });
  }

  setVisible(installButtons, isiOS && !isStandalone());
  installButtons.forEach((button) => button.addEventListener('click', async () => {
    if (installPrompt) {
      const prompt = installPrompt;
      installPrompt = null;
      setVisible(installButtons, false);
      try { await prompt.prompt(); await prompt.userChoice; } catch (_) { /* browser decides */ }
    } else if (isiOS && !isStandalone()) {
      showHelp();
    }
  }));
  window.addEventListener('beforeinstallprompt', (event) => {
    event.preventDefault();
    installPrompt = event;
    if (!isStandalone()) setVisible(installButtons, true);
  });
  window.addEventListener('appinstalled', () => {
    installPrompt = null;
    setVisible(installButtons, false);
  });

  window.addEventListener('load', async () => {
    try {
      const registration = await navigator.serviceWorker.register('/sw.js', {scope: '/', updateViaCache: 'none'});
      const showUpdate = () => setVisible(updateButtons, Boolean(registration.waiting && navigator.serviceWorker.controller));
      showUpdate();
      registration.addEventListener('updatefound', () => {
        const installing = registration.installing;
        if (!installing) return;
        installing.addEventListener('statechange', showUpdate);
      });
      updateButtons.forEach((button) => button.addEventListener('click', () => {
        if (!registration.waiting) return;
        awaitingReload = true;
        registration.waiting.postMessage({type: 'SKIP_WAITING'});
      }));
      navigator.serviceWorker.addEventListener('controllerchange', () => {
        if (awaitingReload) window.location.reload();
      });
    } catch (error) {
      // The website must remain fully operational if installation is blocked.
      console.warn('NORSU PWA registration unavailable:', error);
    }
  });
})();
