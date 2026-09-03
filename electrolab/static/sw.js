const CACHE_NAME = 'electrolab-v4';
const ASSETS = [
    '/static/logo.png',
    '/static/manifest.json'
];

// Instala o Service Worker e guarda a logo
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME).then(cache => cache.addAll(ASSETS))
    );
    self.skipWaiting();
});

self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(keys => Promise.all(
            keys.filter(key => key !== CACHE_NAME).map(key => caches.delete(key))
        ))
    );
    self.clients.claim();
});

// Intercepta as requisições (Carregamento instantâneo)
self.addEventListener('fetch', event => {
    // Se for navegação de página (HTML), mostra o cache na hora e atualiza no fundo
    if (event.request.mode === 'navigate' || event.request.headers.get('accept').includes('text/html')) {
        event.respondWith(
            caches.match(event.request).then(cachedResponse => {
                const networkFetch = fetch(event.request).then(networkResponse => {
                    caches.open(CACHE_NAME).then(cache => cache.put(event.request, networkResponse.clone()));
                    return networkResponse;
                }).catch(() => cachedResponse); // Se estiver sem internet, usa o cache
                
                // Retorna o cache IMEDIATAMENTE se existir, senão espera a rede
                return cachedResponse || networkFetch;
            })
        );
        return;
    }

    // Para imagens e scripts, tenta a rede primeiro
    event.respondWith(
        fetch(event.request).catch(() => caches.match(event.request))
    );
});