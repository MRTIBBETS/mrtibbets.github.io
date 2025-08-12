/**
 * Service Worker for Alexander Tibbets website
 * Provides offline capabilities, caching, and performance improvements
 */

const CACHE_NAME = 'alexander-tibbets-v1.0.0';
const STATIC_CACHE = 'static-v1.0.0';
const DYNAMIC_CACHE = 'dynamic-v1.0.0';

const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/profiles.html',
  '/style.css',
  '/assets/js/common.js',
  '/assets/favicon.ico',
  '/assets/images/banner.png',
  '/assets/icons/apple_music.svg',
  '/assets/icons/bloomberg.svg',
  '/assets/icons/crunchbase.svg',
  '/assets/icons/mixcloud.svg',
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
          cacheNames.map(cacheName => {
            if (cacheName !== STATIC_CACHE && cacheName !== DYNAMIC_CACHE) {
              console.log('Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            }
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
    event.respondWith(networkFirst(request, DYNAMIC_CACHE));
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
    return new Response('Network error', { status: 503 });
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
 * Background sync - handle offline actions
 */
self.addEventListener('sync', event => {
  if (event.tag === 'background-sync') {
    event.waitUntil(doBackgroundSync());
  }
});

/**
 * Perform background sync tasks
 */
async function doBackgroundSync() {
  try {
    console.log('Performing background sync');
    
    // Update cache with new content
    const cache = await caches.open(STATIC_CACHE);
    const requests = await cache.keys();
    
    for (const request of requests) {
      try {
        const response = await fetch(request);
        if (response.ok) {
          await cache.put(request, response);
        }
      } catch (error) {
        console.log('Failed to update cache for:', request.url);
      }
    }
  } catch (error) {
    console.log('Background sync failed:', error);
  }
}

/**
 * Push notifications - handle push events
 */
self.addEventListener('push', event => {
  if (event.data) {
    const data = event.data.json();
    const options = {
      body: data.body,
      icon: '/assets/favicon.ico',
      badge: '/assets/favicon.ico',
      vibrate: [100, 50, 100],
      data: {
        dateOfArrival: Date.now(),
        primaryKey: 1
      }
    };
    
    event.waitUntil(
      self.registration.showNotification(data.title, options)
    );
  }
});

/**
 * Notification click - handle notification interactions
 */
self.addEventListener('notificationclick', event => {
  event.notification.close();
  
  event.waitUntil(
    clients.openWindow('/')
  );
});

/**
 * Error handling - log errors for debugging
 */
self.addEventListener('error', event => {
  console.error('Service worker error:', event.error);
});

/**
 * Unhandled rejection - log promise rejections
 */
self.addEventListener('unhandledrejection', event => {
  console.error('Service worker unhandled rejection:', event.reason);
});
