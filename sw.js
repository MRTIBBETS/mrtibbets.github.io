/**
 * Service Worker for Alexander Tibbets website
 * Provides offline capabilities and performance improvements
 */

const CACHE_NAME = 'alexander-tibbets-v1.0.2';
const STATIC_CACHE = 'static-v1.0.2';

const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/profiles.html',
  '/links.html',
  '/style.css',
  '/assets/js/common.js',
  '/assets/favicon.ico',
  '/assets/images/favicon.svg',
  '/assets/images/icon-192.png',
  '/assets/images/icon-512.png',
  '/assets/images/apple-touch-icon.png',
  '/assets/images/banner.png',
  'https://use.fontawesome.com/releases/v6.4.2/css/all.css'
];

/**
 * Install event - cache static assets
 */
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then(cache => {
        console.log('Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .catch(error => {
        console.log('Failed to cache static assets:', error);
      })
  );
  self.skipWaiting();
});

/**
 * Activate event - clean up old caches
 */
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(cacheNames => {
        return Promise.all(
          cacheNames.filter(cacheName => {
            return cacheName !== STATIC_CACHE;
          }).map(cacheName => {
            console.log('Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          })
        );
      })
      .then(() => {
        console.log('Service worker activated');
        return self.clients.claim();
      })
  );
});

/**
 * Fetch event - intercept requests and serve from cache
 */
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') return;

  // Skip non-HTTP(S) requests
  if (!url.protocol.startsWith('http')) return;

  // Handle different types of requests
  if (url.pathname === '/' || url.pathname.endsWith('.html')) {
    // HTML pages: network first, then cache
    event.respondWith(networkFirst(request, STATIC_CACHE));
  } else if (url.pathname.endsWith('.css') || url.pathname.endsWith('.js')) {
    // CSS/JS: cache first, then network
    event.respondWith(cacheFirst(request, STATIC_CACHE));
  } else if (url.pathname.includes('/assets/') || url.pathname.includes('.ico') || url.pathname.includes('.png') || url.pathname.includes('.svg')) {
    // Static assets: cache first, then network
    event.respondWith(cacheFirst(request, STATIC_CACHE));
  } else if (url.hostname === 'use.fontawesome.com') {
    // External fonts: cache first, then network
    event.respondWith(cacheFirst(request, STATIC_CACHE));
  } else {
    // Other requests: network first, then cache
    event.respondWith(networkFirst(request, STATIC_CACHE));
  }
});

/**
 * Cache first strategy - check cache first, then network
 */
async function cacheFirst(request, cacheName) {
  try {
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      const cache = await caches.open(cacheName);
      cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  } catch (error) {
    console.log('Cache first strategy failed:', error);
    return new Response('Resource not available', { status: 503 });
  }
}

/**
 * Network first strategy - check network first, then cache
 */
async function networkFirst(request, cacheName) {
  try {
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      const cache = await caches.open(cacheName);
      cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  } catch (error) {
    console.log('Network first strategy failed, trying cache:', error);
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    return new Response('Offline content not available', { status: 503 });
  }
}
