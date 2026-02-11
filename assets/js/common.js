/**
 * Common functionality for Alexander Tibbets website
 */

/**
 * Initialize Google Analytics with privacy-focused settings
 */
function initializeAnalytics() {
  if (window.alexanderTibbetsAnalyticsInitialized) return;
  window.alexanderTibbetsAnalyticsInitialized = true;

  window.dataLayer = window.dataLayer || [];
  
  if (!window.gtag) {
    window.gtag = function() {
      window.dataLayer.push(arguments);
    };
  }
  
  window.gtag('js', new Date());
  window.gtag('config', 'G-GGXQFFQVVY', {
    anonymize_ip: true,
    cookie_flags: 'SameSite=None;Secure'
  });
}

/**
 * Track Core Web Vitals performance metrics
 */
function trackPerformance() {
  if (!('PerformanceObserver' in window)) return;
  
  try {
    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (entry.entryType !== 'navigation') continue;

        const loadTime = entry.loadEventEnd - entry.loadEventStart;
        if (loadTime > 0 && window.gtag) {
          window.gtag('event', 'timing_complete', {
            name: 'load',
            value: Math.round(loadTime)
          });
        }
      }
    });
    
    observer.observe({ entryTypes: ['navigation'] });
  } catch (error) {
    console.warn('Performance tracking failed:', error);
  }
}

/**
 * Register Service Worker
 */
function registerServiceWorker() {
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/sw.js')
        .then(registration => {
          console.log('Service worker registered:', registration);
        })
        .catch(error => {
          console.log('Service worker registration failed:', error);
        });
    });
  }
}

/**
 * Initialize all functionality when DOM is ready
 */
function initialize() {
  initializeAnalytics();
  trackPerformance();
  registerServiceWorker();
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', initialize);

// Export functions for external use
window.AlexanderTibbetsWebsite = {
  initializeAnalytics,
  trackPerformance,
  initialize
};
