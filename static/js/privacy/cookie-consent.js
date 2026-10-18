(function () {
  'use strict';
  const root = document.getElementById('norsuCookieConsent');
  const settings = document.getElementById('norsuCookieSettings');
  if (!root || !settings) return;
  const endpoint = root.dataset.consentEndpoint;
  const error = root.querySelector('.norsu-cookie__error');
  function csrfCookie() {
    const part = document.cookie.split('; ').find(x => x.startsWith('csrftoken='));
    return part ? decodeURIComponent(part.slice(10)) : '';
  }
  async function fetchState() {
    const response = await fetch(endpoint, {credentials:'same-origin',cache:'no-store'});
    if (!response.ok) throw new Error('consent state unavailable');
    return response.json();
  }
  function showPreferences() {root.hidden = false;settings.hidden = true;error.hidden = true;}
  function hidePreferences() {root.hidden = true;settings.hidden = false;}
  settings.addEventListener('click', showPreferences);
  root.querySelectorAll('[data-cookie-choice]').forEach(button => {
    button.addEventListener('click', async () => {
      const buttons = root.querySelectorAll('[data-cookie-choice]');
      buttons.forEach(b => {b.disabled = true;});
      error.hidden = true;
      try {
        const body = new URLSearchParams({choice:button.dataset.cookieChoice});
        const response = await fetch(endpoint, {method:'POST',body,credentials:'same-origin',
          headers:{'X-CSRFToken':csrfCookie(),'Content-Type':'application/x-www-form-urlencoded'}});
        if (!response.ok) throw new Error('preference not saved');
        hidePreferences();
      } catch (_) {error.hidden = false;}
      finally {buttons.forEach(b => {b.disabled = false;});}
    });
  });
  fetchState().then(data => {
    if (data.choice === 'necessary' || data.choice === 'analytics') hidePreferences();
    else showPreferences();
  }).catch(() => { // Consent service failure must never block navigation.
    root.hidden = true;settings.hidden = true;
  });
})();
