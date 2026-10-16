/**
 * Service Worker for AI Health Assistant.
 * Caches app shell, stylesheets, javascript logic, and offline emergency assets.
 */

const CACHE_NAME = 'ai-health-assistant-v1';

const APP_SHELL = [
  '/',
  '/index.html',
  '/manifest.json',
  '/css/style.css',
  '/js/api.js',
  '/js/ui.js',
  '/js/auth.js',
  '/js/redflags.js',
  '/js/offline.js',
  '/js/notifications.js',
  '/js/chat.js',
  '/js/result.js',
  '/js/doctors.js',
  '/js/consultations.js',
  '/pages/login.html',
  '/pages/register.html',
  '/pages/patient-dashboard.html',
  '/pages/symptom-check.html',
  '/pages/result.html',
  '/pages/doctors.html',
  '/pages/consultations.html',
  '/pages/doctor-dashboard.html',
  '/pages/doctor-consultation.html',
  '/pages/profile.html',
  '/pages/admin.html'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('[Service Worker] Caching app shell');
      return cache.addAll(APP_SHELL);
    }).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keyList) => {
      return Promise.all(
        keyList.map((key) => {
          if (key !== CACHE_NAME) {
            console.log('[Service Worker] Removing old cache', key);
            return caches.delete(key);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // For API calls, use network first, do not cache auth/sync writes in SW
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(event.request).catch(() => {
        return new Response(JSON.stringify({ ok: false, error: 'Offline - request failed' }), {
          headers: { 'Content-Type': 'application/json' }
        });
      })
    );
    return;
  }

  // Cache-first strategy for app shell assets
  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      if (cachedResponse) {
        // Return cached and update in background
        fetch(event.request).then((networkResponse) => {
          if (networkResponse && networkResponse.status === 200) {
            caches.open(CACHE_NAME).then((cache) => cache.put(event.request, networkResponse));
          }
        }).catch(() => {});
        return cachedResponse;
      }
      return fetch(event.request);
    })
  );
});
