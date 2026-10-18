/* NORSU PWA installation and updates. No telemetry, server writes or push permission. */
(() => {
  'use strict';
  if (!window.isSecureContext || !('serviceWorker' in navigator)) return;
  let installPrompt = null;
  let awaitingReload = false;
  let modalReturnFocus = null;
  const isStandalone = () => window.matchMedia('(display-mode: standalone)').matches || navigator.standalone === true;
  const isiOS = /iphone|ipad|ipod/i.test(navigator.userAgent);
  const isAndroid = /android/i.test(navigator.userAgent);
  let installed = false;
  const installButtons = [...document.querySelectorAll('[data-pwa-install]')];
  const updateButtons = [...document.querySelectorAll('[data-pwa-update]')];
  const help = document.getElementById('norsuPwaHelp');
  const helpPanel = help && help.querySelector('.norsu-pwa-help__panel');
  const helpInstructions = document.getElementById('norsuPwaHelpInstructions');
  const floatingButtons = installButtons.filter((button) => button.classList.contains('norsu-pwa-install-fab'));
  const menuButtons = installButtons.filter((button) => !button.classList.contains('norsu-pwa-install-fab'));
  const consentIsOpen = () => {
    const notice = document.getElementById('norsuCookieConsent');
    return Boolean(notice && !notice.hidden);
  };
  const setVisible = (controls, visible) => controls.forEach((control) => { control.hidden = !visible; });
  const refreshInstallButtons = () => {
    const available = !installed && !isStandalone();
    // A native prompt may not be offered immediately. Keep a functional
    // installation-instructions fallback instead of losing the floating CTA.
    setVisible(menuButtons, available);
    setVisible(floatingButtons, available && !consentIsOpen());
  };
  document.addEventListener('norsu:cookie-visibility-changed', refreshInstallButtons);
  const showHelp = () => {
    if (!help) return;
    modalReturnFocus = document.activeElement;
    if (helpInstructions) {
      helpInstructions.textContent = isiOS
        ? 'In Safari, tap Share, then choose Add to Home Screen. Open as Web App if offered.'
        : isAndroid
          ? 'In your browser menu, choose Install app or Add to Home screen when available. If it is unavailable, try Chrome outside private browsing.'
          : 'Look for Install app or Install page as app in your browser menu or address bar. Some browsers and private windows do not support installation.';
    }
    help.hidden = false;
    if (helpPanel) helpPanel.focus();
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

  refreshInstallButtons();
  installButtons.forEach((button) => button.addEventListener('click', async () => {
    if (installPrompt) {
      const prompt = installPrompt;
      installPrompt = null;
      try {
        await prompt.prompt();
        const choice = await prompt.userChoice;
        if (choice && choice.outcome === 'accepted') {
          // appinstalled will confirm completion; until then the controls stay
          // available to show instructions if installation never completes.
        }
      } catch (_) { /* Native prompt may be cancelled or unavailable. */ }
      refreshInstallButtons();
    } else if (!isStandalone()) {
      showHelp();
    }
  }));
  window.addEventListener('beforeinstallprompt', (event) => {
    event.preventDefault();
    installPrompt = event;
    refreshInstallButtons();
  });
  window.addEventListener('appinstalled', () => {
    installPrompt = null;
    installed = true;
    refreshInstallButtons();
  });

  window.addEventListener('load', async () => {
    try {
      const registration = await navigator.serviceWorker.register('/sw.js', {scope: '/', updateViaCache: 'none'});
      refreshInstallButtons();
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
