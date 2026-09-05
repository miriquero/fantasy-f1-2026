/* Service worker del torneo.
 *
 * Estrategia deliberada, distinta segun el tipo de archivo:
 *
 *   - La pagina (ranking_f1.html) va POR RED PRIMERO. El ranking se
 *     actualiza dos veces por dia; si se sirviera desde cache, alguien podria
 *     abrir el sitio despues de una carrera y ver la tabla vieja sin
 *     enterarse. Solo si no hay red se cae al cache.
 *   - Las tipografias y los iconos van POR CACHE PRIMERO: no cambian nunca y
 *     son lo que mas tarda en un telefono con mala señal.
 *
 * Al cambiar VERSION se descartan los caches viejos.
 */

var VERSION = 'fantasy-f1-v1';
var ESENCIALES = ['ranking_f1.html', 'manifest.json', 'img/favicon-512.png'];

self.addEventListener('install', function (evento) {
    evento.waitUntil(
        caches.open(VERSION)
            .then(function (cache) { return cache.addAll(ESENCIALES); })
            .catch(function () { /* si falla, el sitio anda igual, sin offline */ })
    );
    self.skipWaiting();
});

self.addEventListener('activate', function (evento) {
    evento.waitUntil(
        caches.keys().then(function (nombres) {
            return Promise.all(nombres.map(function (n) {
                if (n !== VERSION) { return caches.delete(n); }
            }));
        }).then(function () { return self.clients.claim(); })
    );
});

self.addEventListener('fetch', function (evento) {
    var pedido = evento.request;
    if (pedido.method !== 'GET') { return; }

    var url = new URL(pedido.url);
    var esTipografia = url.hostname.indexOf('fonts.') === 0 ||
                       url.hostname.indexOf('fonts.g') !== -1;
    var esImagen = /\.(png|ico|svg|jpg|webp)$/i.test(url.pathname);

    if (esTipografia || esImagen) {
        evento.respondWith(
            caches.match(pedido).then(function (guardado) {
                return guardado || fetch(pedido).then(function (respuesta) {
                    var copia = respuesta.clone();
                    caches.open(VERSION).then(function (c) { c.put(pedido, copia); });
                    return respuesta;
                });
            })
        );
        return;
    }

    evento.respondWith(
        fetch(pedido).then(function (respuesta) {
            var copia = respuesta.clone();
            caches.open(VERSION).then(function (c) { c.put(pedido, copia); });
            return respuesta;
        }).catch(function () {
            return caches.match(pedido).then(function (guardado) {
                return guardado || caches.match('ranking_f1.html');
            });
        })
    );
});
