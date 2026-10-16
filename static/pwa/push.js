/* Web push is strictly opt-in. Do not show browser permission on page load. */
(() => {
  'use strict';
  const enable = [...document.querySelectorAll('[data-pwa-push-enable]')];
  const disable = [...document.querySelectorAll('[data-pwa-push-disable]')];
  const status = document.querySelector('[data-pwa-push-status]');
  const compatible = window.isSecureContext && 'serviceWorker' in navigator &&
    'PushManager' in window && 'Notification' in window;
  if (!compatible || !(enable.length || disable.length)) return;
  let publicKey = '';
  let busy = false;
  const setVis = (els, show) => els.forEach((el) => {el.hidden = !show;});
  const notice = (message) => {
    if (!status) return;
    status.textContent = message;
    status.hidden = false;
  };
  const csrf = () => document.querySelector('meta[name="csrf-token"]')?.content ||
    document.querySelector('[name="csrfmiddlewaretoken"]')?.value || '';
  const request = async (url, payload) => {
    const result = await fetch(url, {
      method: 'POST', credentials: 'same-origin',
      headers: {'Content-Type': 'application/json', 'X-CSRFToken': csrf()},
      body: JSON.stringify(payload)
    });
    if (!result.ok) throw new Error('Could not save notification settings (' + result.status + ').');
    return result.json();
  };
  const toBytes = (base64) => {
    const padded = (base64 + '='.repeat((4 - base64.length % 4) % 4)).replace(/-/g, '+').replace(/_/g, '/');
    return Uint8Array.from(atob(padded), (character) => character.charCodeAt(0));
  };
  const getSubscription = async () => {
    const reg = await navigator.serviceWorker.ready;
    return {reg, subscription: await reg.pushManager.getSubscription()};
  };
  const refresh = async () => {
    try {
      const {subscription} = await getSubscription();
      setVis(enable, !subscription && Notification.permission !== 'denied');
      setVis(disable, Boolean(subscription));
    } catch (_) { setVis(enable, false); setVis(disable, false); }
  };
  const run = async (func) => {
    if (busy) return;
    busy = true;
    try { await func(); } catch (error) { notice(error.message || 'Notification settings could not be updated.'); }
    finally { busy = false; await refresh(); }
  };
  enable.forEach((el) => el.addEventListener('click', () => run(async () => {
    if (!publicKey) return;
    // Permission is requested ONLY in direct response to the user choosing Enable.
    if (Notification.permission === 'denied') throw new Error('Enable NORSU notifications in browser settings.');
    const result = await Notification.requestPermission();
    if (result !== 'granted') { notice('Notifications were not enabled.'); return; }
    const {reg} = await getSubscription();
    let subscription = await reg.pushManager.getSubscription();
    if (!subscription) subscription = await reg.pushManager.subscribe({userVisibleOnly: true, applicationServerKey: toBytes(publicKey)});
    await request('/api/pwa/push/subscribe/', subscription.toJSON());
    notice('NORSU push alerts enabled on this device.');
  })));
  disable.forEach((el) => el.addEventListener('click', () => run(async () => {
    const {subscription} = await getSubscription();
    if (subscription) {
      await request('/api/pwa/push/unsubscribe/', {endpoint: subscription.endpoint});
      await subscription.unsubscribe();
    }
    notice('NORSU push alerts disabled on this device.');
  })));
  // Only re-associate an existing opted-in browser subscription with the current user.
  // Never silently create a subscription or request OS permission on load.
  window.addEventListener('load', async () => {
    try {
      const response = await fetch('/api/pwa/push/config/', {credentials:'same-origin', cache:'no-store'});
      if (!response.ok) return;
      const config = await response.json();
      if (!config.enabled || !config.publicKey) return;
      publicKey = config.publicKey;
      const {subscription} = await getSubscription();
      if (subscription) {
        try { await request('/api/pwa/push/subscribe/', subscription.toJSON()); }
        catch (error) { notice(error.message); }
      }
      await refresh();
    } catch (_) { /* Feature is progressive enhancement; never affect app navigation. */ }
  });
})();
