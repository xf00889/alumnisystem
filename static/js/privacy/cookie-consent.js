(function () {
  'use strict';

  function startCookieConsent() {
    const root = document.getElementById('norsuCookieConsent');
    const settingsButton = document.getElementById('norsuCookieSettings');
    if (!root || !settingsButton) return;

    const endpoint = root.dataset.consentEndpoint;
    const error = root.querySelector('.norsu-cookie__error');
    const buttons = Array.from(root.querySelectorAll('[data-cookie-choice]'));
    let csrfToken = '';

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
      error.hidden = true;
    }

    async function ensureCsrfToken(forceRefresh) {
      if (!forceRefresh) {
        csrfToken = csrfToken || cookieValue('csrftoken');
        if (csrfToken) return csrfToken;
      }
      const response = await fetch(endpoint, {
        method: 'GET',
        credentials: 'same-origin',
        cache: 'no-store',
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
      });
      if (!response.ok) throw new Error('Unable to prepare privacy request');
      const payload = await response.json().catch(function () { return {}; });
      csrfToken = payload.csrfToken || cookieValue('csrftoken') || '';
      if (!csrfToken) throw new Error('Missing CSRF token');
      return csrfToken;
    }

    async function submitChoice(choice, token) {
      return fetch(endpoint, {
        method: 'POST',
        body: new URLSearchParams({ choice: choice }),
        credentials: 'same-origin',
        cache: 'no-store',
        headers: {
          'X-CSRFToken': token,
          'X-Requested-With': 'XMLHttpRequest',
          'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
        }
      });
    }

    async function saveChoice(choice) {
      let token = await ensureCsrfToken(false);
      let response = await submitChoice(choice, token);
      if (response.status === 403) {
        token = await ensureCsrfToken(true);
        response = await submitChoice(choice, token);
      }
      if (!response.ok) {
        const payload = await response.json().catch(function () { return {}; });
        throw new Error(payload.error || 'Preference was not saved');
      }
      const result = await response.json();
      if (result.choice !== choice) throw new Error('Unexpected preference');
      hidePreferences();
    }

    settingsButton.addEventListener('click', showPreferences);

    buttons.forEach(function (button) {
      button.addEventListener('click', async function () {
        buttons.forEach(function (control) { control.disabled = true; });
        error.hidden = true;
        try {
          await saveChoice(button.dataset.cookieChoice);
        } catch (_) {
          showPreferences();
          error.hidden = false;
        } finally {
          buttons.forEach(function (control) { control.disabled = false; });
        }
      });
    });

    if (!root.hidden) {
      ensureCsrfToken(false).catch(function () { /* handled when user clicks */ });
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', startCookieConsent, { once: true });
  } else {
    startCookieConsent();
  }
})();
