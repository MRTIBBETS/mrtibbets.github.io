/**
 * Service Worker for Alexander Tibbets website
 * Provides offline capabilities and performance improvements
 */

const STATIC_CACHE = 'static-v1.0.7';

const CRITICAL_ASSETS = [
  '/',
  '/index.html',
  '/profiles.html',
  '/links.html',
  '/assets/js/common.js?v=common1',
  '/assets/favicon.ico?v=assets1',
  '/assets/images/favicon.svg?v=assets1',
  '/assets/images/icon-192.png?v=assets1',
  '/assets/images/icon-512.png?v=assets1',
  '/assets/images/apple-touch-icon.png?v=assets1',
  '/assets/images/banner.png?v=assets1',
  'https://use.fontawesome.com/releases/v6.4.2/css/all.css'
];

const STATIC_ASSETS = [...CRITICAL_ASSETS];

/**
 * Install event - cache static assets
 */
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then(async cache => {
        console.log('Caching static assets');
        try {
          await cache.addAll(STATIC_ASSETS);
        } catch (error) {
          console.error('Asset caching failed:', error);
          throw error;
        }
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
    // HTML pages: stale-while-revalidate strategy for instant load
    event.respondWith(staleWhileRevalidate(event, request, STATIC_CACHE));
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

/**
 * Stale-while-revalidate strategy - serve from cache, then update from network
 */
async function staleWhileRevalidate(event, request, cacheName) {
  const cache = await caches.open(cacheName);

  // Start network request immediately (parallel)
  const networkFetch = fetch(request).then(response => {
    if (response.ok) {
      cache.put(request, response.clone());
    }
    return response;
  });

  // Keep SW alive for the fetch itself
  event.waitUntil(networkFetch.catch(err => console.log('SWR background fetch failed', err)));

  // Check cache
  const cachedResponse = await cache.match(request);
  if (cachedResponse) {
    return cachedResponse;
  }

  try {
    return await networkFetch;
  } catch (error) {
    console.log('SWR network fallback failed:', error);
    return new Response('Offline content not available', { status: 503 });
  }
}
