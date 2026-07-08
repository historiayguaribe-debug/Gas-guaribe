const CACHE_NAME = 'gasguaribe-v1';
const urlsToCache = [
    'index.html',
    'recogidas.html',
    'entregas.html',
    'inventario.html',
    'ventas.html',
    'gastos.html',
    'reportes.html',
    'configuracion.html',
    'style.css',
    'app.js',
    'manifest.json'
];

self.addEventListener('install', function(event) {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(function(cache) {
                return cache.addAll(urlsToCache);
            })
    );
});

self.addEventListener('fetch', function(event) {
    event.respondWith(
        caches.match(event.request)
            .then(function(response) {
                if (response) {
                    return response;
                }
                return fetch(event.request);
            })
    );
});
