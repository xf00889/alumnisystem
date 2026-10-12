/* On-demand preview only; the full Notifications page owns read-state management. */
(() => {
  'use strict';
  const toggle = document.getElementById('alumniNotificationsToggle');
  const list = document.getElementById('alumniNotificationPreview');
  if (!toggle || !list) return;
  const allUrl = document.querySelector('.alumni-notification-menu__all')?.href || '/notifications/';

  function status(text) {
    const note = document.createElement('p');
    note.className = 'alumni-notification-menu__empty';
    note.textContent = text;
    list.replaceChildren(note);
  }
  function safeUrl(input) {
    try {
      const url = new URL(input || allUrl, window.location.origin);
      if (url.origin === window.location.origin && ['http:', 'https:'].includes(url.protocol)) {
        return url.pathname + url.search + url.hash;
      }
    } catch (_) { /* use the full list */ }
    return allUrl;
  }
  async function refresh() {
    status('Loading notifications…');
    try {
      const response = await fetch('/api/notifications/?limit=5&offset=0', {
        credentials: 'same-origin', cache: 'no-store', headers: {'Accept':'application/json'}
      });
      if (!response.ok || !(response.headers.get('content-type') || '').includes('application/json')) {
        throw new Error('Notifications are temporarily unavailable.');
      }
      const payload = await response.json();
      if (!payload.success || !Array.isArray(payload.notifications)) throw new Error('Could not load notifications.');
      // The API already excludes new_message: message counts belong in the Messages tab.
      const items = payload.notifications.filter(item => item.notification_type !== 'new_message');
      if (!items.length) {status('You have no recent notifications.');return;}
      const fragment = document.createDocumentFragment();
      items.forEach(item => {
        const link = document.createElement('a');
        link.className = 'alumni-notification-menu__entry' + (item.is_read ? '' : ' is-unread');
        link.href = safeUrl(item.action_url);
        const title = document.createElement('strong');
        title.className = 'alumni-notification-menu__title';
        title.textContent = item.title || 'New notification';
        const message = document.createElement('span');
        message.className = 'alumni-notification-menu__message';
        message.textContent = item.message || '';
        link.append(title,message);
        fragment.append(link);
      });
      list.replaceChildren(fragment);
    } catch (error) {status(error.message || 'Unable to load notifications.');}
  }
  // Clicking the bell uses Bootstrap's accessible dropdown; load only when shown.
  toggle.addEventListener('shown.bs.dropdown', refresh);
})();
