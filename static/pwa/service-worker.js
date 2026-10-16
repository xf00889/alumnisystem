/* NORSU PWA: intentionally minimal and privacy-first.
 * There is NO HTML, API, message, document, attachment, or media response caching.
 * Never intercept POST or non-GET methods; leave authentication entirely on the server.
 * Bump SHELL_CACHE when packaged offline assets change.
 */
'use strict';
const SHELL_CACHE = 'norsu-pwa-shell-v1';
const CACHE_PREFIX = 'norsu-pwa-shell-';
const OFFLINE_PAGE = '/static/pwa/offline.html';
const SHELL_ASSETS = Object.freeze([
  OFFLINE_PAGE,
  '/static/pwa/icons/icon-192.png',
  '/static/pwa/icons/icon-512.png',
  '/static/pwa/icons/icon-maskable-192.png',
  '/static/pwa/icons/icon-maskable-512.png',
  '/static/pwa/icons/apple-touch-icon.png'
]);

self.addEventListener('install', (event) => {
  // A transient failure to fetch an icon must not prevent worker installation.
  event.waitUntil(caches.open(SHELL_CACHE).then((cache) =>
    Promise.allSettled(SHELL_ASSETS.map((path) => cache.add(path)))
  ));
  // No skipWaiting here: an active transaction must not be interrupted by an update.
});

self.addEventListener('activate', (event) => {
  event.waitUntil((async () => {
    const names = await caches.keys();
    await Promise.all(names.filter((name) => name.startsWith(CACHE_PREFIX) && name !== SHELL_CACHE)
      .map((name) => caches.delete(name)));
    await self.clients.claim();
  })());
});

self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});

self.addEventListener('fetch', (event) => {
  const request = event.request;
  if (request.method !== 'GET') return;
  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  if (request.mode === 'navigate') {
    event.respondWith((async () => {
      try {
        // Server always authorizes every page. No navigation is ever persisted.
        return await fetch(request);
      } catch (_) {
        return (await caches.match(OFFLINE_PAGE)) || new Response(
          '<!doctype html><html lang="en"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Offline — NORSU Alumni</title><body><h1>You are offline</h1><p>Connect to the internet and try again.</p><a href="/">Retry</a></body></html>',
          {headers: {'Content-Type': 'text/html; charset=utf-8'}}
        );
      }
    })());
    return;
  }

  // Only explicit public shell assets are cached. NEVER cache arbitrary /static,
  // /media, endpoints, authenticated responses or third-party resources.
  if (SHELL_ASSETS.includes(url.pathname)) {
    event.respondWith(caches.match(url.pathname).then((cached) => cached || fetch(request)));
  }
});
