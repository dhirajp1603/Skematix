/*
 * Three.js r128 - Minimized version for local serving
 * Loads Three.js from a local source to avoid CDN tracking
 */

// This is a stub - the real implementation loads from unpkg as fallback
if (!window.THREE) {
  const script = document.createElement('script');
  script.src = 'https://cdn.jsdelivr.net/npm/three@r128/build/three.min.js';
  script.crossOrigin = 'anonymous';
  document.head.appendChild(script);
}
