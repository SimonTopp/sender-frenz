const CACHE = "frenz-v1";

const SHELL = [
  "/",
  "/index.html",
  "/style.css",
  "/ui.js",
  "/app.js",
  "/avatar.js",
  "/actions.js",
  "/level_up.js",
  "/manifest.json",
  "/icons/icon-192.png",
  "/icons/icon-512.png",
];

const API_PATHS = ["/session/", "/action/", "/level-up", "/avatar/", "/events/"];

function isApi(url) {
  const path = new URL(url).pathname;
  return API_PATHS.some((p) => path.startsWith(p));
}

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)));
  self.skipWaiting();
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
      )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (e) => {
  if (isApi(e.request.url)) return; // network-only for API + SSE
  e.respondWith(
    caches.match(e.request).then((cached) => cached || fetch(e.request))
  );
});
