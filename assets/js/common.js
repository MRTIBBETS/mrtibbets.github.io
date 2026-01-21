/**
 * Common functionality for Alexander Tibbets website
 * Consolidates shared JavaScript functionality to eliminate duplication
 */

/**
 * Initialize Google Analytics with privacy-focused settings
 */
function initializeAnalytics() {
  window.dataLayer = window.dataLayer || [];
  
  function gtag() {
    dataLayer.push(arguments);
  }
  
  gtag('js', new Date());
  gtag('config', 'G-GGXQFFQVVY', {
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
        if (entry.entryType === 'navigation') {
          const loadTime = entry.loadEventEnd - entry.loadEventStart;
          if (loadTime > 0 && window.gtag) {
            gtag('event', 'timing_complete', {
              name: 'load',
              value: Math.round(loadTime)
            });
          }
        }
      }
    });
    
    observer.observe({ entryTypes: ['navigation'] });
  } catch (error) {
    console.warn('Performance tracking failed:', error);
  }
}

/**
 * Enhance keyboard navigation for social media links
 */
function enhanceAccessibility() {
  const socialLinks = document.querySelectorAll('.social-media a');
  
  socialLinks.forEach(link => {
    link.addEventListener('keydown', (event) => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        link.click();
      }
    });
  });
}

/**
 * Initialize all functionality when DOM is ready
 */
function initialize() {
  enhanceAccessibility();
  trackPerformance();
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', initialize);

// Export functions for external use
window.AlexanderTibbetsWebsite = {
  initializeAnalytics,
  trackPerformance,
  enhanceAccessibility,
  initialize
};
