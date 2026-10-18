(function () {
  'use strict';

  function startCookieConsent() {
    const root = document.getElementById('norsuCookieConsent');
    if (!root) return;

    const endpoint = root.dataset.consentEndpoint;
    const error = root.querySelector('.norsu-cookie__error');
    const buttons = Array.from(root.querySelectorAll('[data-cookie-choice]'));
    const closeButton = document.getElementById('norsuCookieClose');
    let csrfToken = '';
    let hasSavedChoice = root.hidden;

    function cookieValue(name) {
      const part = document.cookie.split('; ').find(item => item.startsWith(name + '='));
      return part ? decodeURIComponent(part.slice(name.length + 1)) : '';
    }

    function showPreferences() {
      root.hidden = false;
      if (error) error.hidden = true;
      if (closeButton) closeButton.hidden = !hasSavedChoice;
    }

    function dismissPreferences() {
      root.hidden = true;
      if (error) error.hidden = true;
      if (closeButton) closeButton.hidden = true;
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
        throw new Error('Preference was not saved');
      }
      const result = await response.json();
      if (result.choice !== choice) throw new Error('Unexpected preference');
      hasSavedChoice = true;
      // After either choice, remove all floating controls. Preferences remain
      // available from the footer link rather than a persistent on-screen chip.
      dismissPreferences();
    }

    if (closeButton) {
      closeButton.addEventListener('click', function () {
        if (hasSavedChoice) dismissPreferences();
      });
    }

    document.addEventListener('click', function (event) {
      const link = event.target.closest('[data-norsu-cookie-preferences]');
      if (!link) return;
      event.preventDefault();
      showPreferences();
    });

    buttons.forEach(function (button) {
      button.addEventListener('click', async function () {
        buttons.forEach(function (control) { control.disabled = true; });
        if (error) error.hidden = true;
        try {
          await saveChoice(button.dataset.cookieChoice);
        } catch (_) {
          showPreferences();
          if (error) error.hidden = false;
        } finally {
          buttons.forEach(function (control) { control.disabled = false; });
        }
      });
    });

    // Allows a footer link from another page to open the settings without a
    // permanently floating button, including when the visitor already consented.
    const params = new URLSearchParams(window.location.search);
    if (params.get('cookie-settings') === '1') {
      showPreferences();
      params.delete('cookie-settings');
      const query = params.toString();
      const cleanUrl = window.location.pathname + (query ? '?' + query : '') + window.location.hash;
      window.history.replaceState(window.history.state, '', cleanUrl);
    }

    if (!root.hidden) {
      ensureCsrfToken(false).catch(function () { /* Retried on user selection */ });
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', startCookieConsent, { once: true });
  } else {
    startCookieConsent();
  }
})();
