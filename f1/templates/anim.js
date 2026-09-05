
// Animaciones y micro-interacciones del dashboard
(function() {
    function moveIndicator(btn) {
        var nav = document.querySelector('.tab-nav-inner');
        var indicator = document.getElementById('tab-indicator');
        if (!nav || !indicator || !btn) return;
        var navRect = nav.getBoundingClientRect();
        var btnRect = btn.getBoundingClientRect();
        indicator.style.left = (btnRect.left - navRect.left + nav.scrollLeft) + 'px';
        indicator.style.width = btnRect.width + 'px';
    }

    function animateCount(el) {
        if (el.dataset.counted) return;
        el.dataset.counted = '1';
        var raw = (el.textContent || '0').trim();
        var target = parseFloat(raw.replace(',', '.'));
        if (isNaN(target)) return;
        var isDecimal = raw.indexOf('.') !== -1 || raw.indexOf(',') !== -1;
        var start = null;
        var duration = 800;
        function step(ts) {
            if (!start) start = ts;
            var progress = Math.min((ts - start) / duration, 1);
            var eased = 1 - Math.pow(1 - progress, 3);
            var current = target * eased;
            el.textContent = isDecimal ? current.toFixed(1) : Math.round(current);
            if (progress < 1) { requestAnimationFrame(step); }
            else { el.textContent = isDecimal ? target.toFixed(1) : target; }
        }
        requestAnimationFrame(step);
    }

    function revealPanel(panel) {
        if (!panel) return;
        var items = panel.querySelectorAll('.reveal:not(.visible), .row-reveal:not(.visible)');
        items.forEach(function(el, i) {
            setTimeout(function() { el.classList.add('visible'); }, i * 35);
        });
        var counters = panel.querySelectorAll('[data-countup]:not([data-counted])');
        counters.forEach(function(el, i) {
            setTimeout(function() { animateCount(el); }, 150 + i * 60);
        });
    }

    function bouncePodium() {
        document.querySelectorAll('.podium-card').forEach(function(el) {
            el.classList.remove('podium-enter');
            void el.offsetWidth;
            el.classList.add('podium-enter');
        });
    }

    function popBadges() {
        var cards = document.querySelectorAll('#panel-logros .logro-card:not(.badge-pop)');
        cards.forEach(function(el, i) {
            setTimeout(function() { el.classList.add('badge-pop'); }, i * 35);
        });
    }

    var originalOpenTab = window.openTab;
    window.openTab = function(evt, panelId) {
        originalOpenTab(evt, panelId);
        moveIndicator(evt.currentTarget);
        var panel = document.getElementById(panelId);
        revealPanel(panel);
        if (panelId === 'panel-acumulado') bouncePodium();
        if (panelId === 'panel-logros') popBadges();
    };

    function init() {
        var activeBtn = document.querySelector('.tab-btn.active');
        moveIndicator(activeBtn);
        revealPanel(document.querySelector('.tab-panel.active'));
        bouncePodium();
        window.addEventListener('resize', function() {
            moveIndicator(document.querySelector('.tab-btn.active'));
        });
    }
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
