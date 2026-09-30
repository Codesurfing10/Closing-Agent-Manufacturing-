/* Closing Agent PWA — shell cache + network-first API */
const CACHE_VERSION = "ca-shell-v1";
const SHELL_URLS = [
  "./",
  "./index.html",
  "./style.css",
  "./app.js",
  "./manifest.webmanifest",
  "./icons/icon-192.png",
  "./icons/icon-512.png",
  "./icons/apple-touch-icon.png",
];

const API_HOST = "closing-agent-manufacturing.onrender.com";

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_VERSION).then((cache) => cache.addAll(SHELL_URLS)).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_VERSION).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

function isApiRequest(url) {
  return url.hostname === API_HOST;
}

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET") return;

  const url = new URL(req.url);

  // Network-first for live API — never break online API with stale cache
  if (isApiRequest(url)) {
    event.respondWith(
      fetch(req)
        .then((res) => res)
        .catch(() =>
          new Response(JSON.stringify({ detail: "Offline — API unreachable" }), {
            status: 503,
            headers: { "Content-Type": "application/json" },
          })
        )
    );
    return;
  }

  // Same-origin (or relative) shell: cache-first, network fallback, then cache update
  const sameOrigin = url.origin === self.location.origin;
  if (!sameOrigin) return; // leave CDN (e.g. feather icons) to browser

  event.respondWith(
    caches.match(req).then((cached) => {
      const network = fetch(req)
        .then((res) => {
          if (res && res.ok) {
            const copy = res.clone();
            caches.open(CACHE_VERSION).then((cache) => cache.put(req, copy));
          }
          return res;
        })
        .catch(() => cached);
      return cached || network;
    })
  );
});
