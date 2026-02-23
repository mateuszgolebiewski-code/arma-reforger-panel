const CACHE_NAME = 'arma-panel-v2';

// Przy instalacji — nie cachujemy nic (panel musi być zawsze live)
self.addEventListener('install', event => {
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.map(key => caches.delete(key)))
    )
  );
  self.clients.claim();
});

// Sieć zawsze pierwsza — panel musi pokazywać aktualne dane
self.addEventListener('fetch', event => {
  event.respondWith(
    fetch(event.request).catch(() =>
      caches.match(event.request)
    )
  );
});