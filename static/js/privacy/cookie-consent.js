(function () {
  'use strict';
  function startCookieConsent() {
    const root = document.getElementById('norsuCookieConsent');
    const settingsButton = document.getElementById('norsuCookieSettings');
    if (!root || !settingsButton) return;
    const endpoint = root.dataset.consentEndpoint;
    const error = root.querySelector('.norsu-cookie__error');
    const buttons = Array.from(root.querySelectorAll('[data-cookie-choice]'));
    function cookieValue(name) {
      const part = document.cookie.split('; ').find(item => item.startsWith(name + '='));
      return part ? decodeURIComponent(part.slice(name.length + 1)) : '';
    }
    function showPreferences() {
      root.hidden = false;
      settingsButton.hidden = true;
      error.hidden = true;
    }
    function hidePreferences() {
      root.hidden = true;
      settingsButton.hidden = false;
    }
    settingsButton.addEventListener('click', showPreferences);
    buttons.forEach(button => button.addEventListener('click', async function () {
      buttons.forEach(control => { control.disabled = true; });
      error.hidden = true;
      try {
        // This GET also makes Django's CSRF cookie available to a first-time visitor.
        // It is not needed for the banner to appear: visibility is server-rendered.
        if (!cookieValue('csrftoken')) {
          const bootstrap = await fetch(endpoint, { credentials: 'same-origin', cache: 'no-store' });
          if (!bootstrap.ok) throw new Error('Unable to prepare request');
        }
        const response = await fetch(endpoint, {
          method: 'POST',
          body: new URLSearchParams({ choice: button.dataset.cookieChoice }),
          credentials: 'same-origin',
          cache: 'no-store',
          headers: {
            'X-CSRFToken': cookieValue('csrftoken'),
            'Content-Type': 'application/x-www-form-urlencoded'
          }
        });
        if (!response.ok) throw new Error('Preference was not saved');
        const result = await response.json();
        if (result.choice !== button.dataset.cookieChoice) throw new Error('Unexpected preference');
        hidePreferences();
      } catch (_) {
        // Never silently dismiss an unrecorded preference.
        showPreferences();
        error.hidden = false;
      } finally {
        buttons.forEach(control => { control.disabled = false; });
      }
    }));
    // Do not hide a notice just because a GET status check fails or is blocked.
    // The initial UI is rendered by Django from the signed consent cookie.
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', startCookieConsent, { once: true });
  } else {
    startCookieConsent();
  }
})();
