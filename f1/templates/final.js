// ===== PESTAÑA FINAL =====
// Se revela sola cuando termina la temporada (data-terminada="1"). Antes,
// con ?final=1 en la dirección se ve una vista previa con los datos de hoy.
(function () {
    var panel = document.getElementById('panel-final');
    if (!panel) return;
    var terminada = panel.getAttribute('data-terminada') === '1';
    var previa = /[?&]final=1\b/.test(location.search);
    var revelado = panel.querySelector('.fin-revelado');

    // Fecha de la última carrera en el horario del que mira.
    panel.querySelectorAll('[data-fecha]').forEach(function (el) {
        var iso = el.getAttribute('data-fecha');
        if (!iso) return;
        var d = new Date(iso);
        el.textContent = d.toLocaleDateString('es-AR', { weekday: 'long', day: 'numeric', month: 'long' })
            + ', ' + d.toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit', hourCycle: 'h23' });
    });

    if (!terminada && previa && revelado) {
        revelado.hidden = false;
        // En la vista previa se ve como el día de la final: sin el cartel de espera.
        var espera = panel.querySelector('.fin-espera');
        if (espera) espera.hidden = true;
        var aviso = document.createElement('p');
        aviso.className = 'fin-vista-previa';
        aviso.textContent = 'Vista previa: así se vería la Final si la temporada terminara hoy. La familia todavía no la ve.';
        revelado.insertBefore(aviso, revelado.firstChild);
    }
    var visible = revelado && !revelado.hidden;

    // Con la temporada terminada (o en vista previa), la página abre en la Final.
    var boton = document.querySelector('.tab-btn[onclick*="panel-final"]');
    if (boton && (terminada || previa)) {
        setTimeout(function () {
            boton.click();
            // La barra de pestañas se desplaza con animación: cuando termina,
            // se reacomoda el indicador rojo (si no, queda debajo de otra).
            setTimeout(function () { window.dispatchEvent(new Event('resize')); }, 700);
        }, 0);
    }

    // El podio sube (y cae el confeti) recién cuando se lo ve en pantalla.
    var podio = panel.querySelector('.fin-podio');
    if (podio && visible) {
        podio.classList.add('fin-oculto');
        var animado = false;
        var arrancar = function () {
            if (animado) return;
            animado = true;
            podio.classList.remove('fin-oculto');
            podio.classList.add('fin-animar');
            setTimeout(function () { confeti(podio.getAttribute('data-confeti')); }, 2200);
        };
        if ('IntersectionObserver' in window) {
            new IntersectionObserver(function (entradas, obs) {
                if (entradas.some(function (e) { return e.isIntersecting; })) { obs.disconnect(); arrancar(); }
            }, { threshold: 0.4 }).observe(podio);
        } else {
            arrancar();
        }
    }

    function confeti(color) {
        if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
        var lienzo = document.createElement('canvas');
        lienzo.className = 'fin-confeti';
        document.body.appendChild(lienzo);
        var ctx = lienzo.getContext('2d');
        var W = lienzo.width = window.innerWidth, H = lienzo.height = window.innerHeight;
        var colores = [color || '#FFD700', '#FFD700', '#FFFFFF', color || '#E10600'];
        var piezas = [];
        for (var i = 0; i < 160; i++) {
            piezas.push({ x: Math.random() * W, y: -20 - Math.random() * H * 0.5,
                          vx: (Math.random() - 0.5) * 2, vy: 2 + Math.random() * 3,
                          r: Math.random() * Math.PI, vr: (Math.random() - 0.5) * 0.2,
                          w: 6 + Math.random() * 6, h: 3 + Math.random() * 4,
                          c: colores[i % colores.length] });
        }
        var inicio = performance.now();
        function cuadro(t) {
            ctx.clearRect(0, 0, W, H);
            piezas.forEach(function (p) {
                p.x += p.vx; p.y += p.vy; p.r += p.vr;
                ctx.save(); ctx.translate(p.x, p.y); ctx.rotate(p.r);
                ctx.fillStyle = p.c; ctx.fillRect(-p.w / 2, -p.h / 2, p.w, p.h); ctx.restore();
            });
            if (t - inicio < 4500) requestAnimationFrame(cuadro); else lienzo.remove();
        }
        requestAnimationFrame(cuadro);
    }
})();

function finMostrar(i) {
    document.querySelectorAll('.fin-tarjeta').forEach(function (t) { t.hidden = String(t.getAttribute('data-i')) !== String(i); });
    document.querySelectorAll('.fin-chip').forEach(function (c, j) { c.classList.toggle('activo', j === i); });
    var bajar = document.getElementById('fin-bajar');
    if (bajar) bajar.hidden = false;
}

function finBajar() {
    var tarjeta = document.querySelector('.fin-tarjeta:not([hidden])');
    if (!tarjeta || typeof html2canvas === 'undefined') return;
    html2canvas(tarjeta, { backgroundColor: '#080808', scale: 2 }).then(function (lienzo) {
        var nombre = (tarjeta.querySelector('.fin-tarjeta-nombre') || {}).textContent || 'tarjeta';
        var a = document.createElement('a');
        a.download = 'mi-temporada-2026-' + nombre.trim().replace(/[^a-z0-9]+/gi, '-').toLowerCase() + '.png';
        a.href = lienzo.toDataURL('image/png');
        a.click();
    });
}
