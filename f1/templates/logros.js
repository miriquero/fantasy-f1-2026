
// Animar barras de progreso al activar la pestaña de logros
(function() {
    var originalOpenTab = window.openTab;
    window.openTab = function(evt, panelId) {
        originalOpenTab(evt, panelId);
        if (panelId === 'panel-logros') {
            document.querySelectorAll('.logros-lider-bar-fill').forEach(function(el) {
                var w = el.style.width;
                el.style.width = '0';
                setTimeout(function() { el.style.width = w; }, 80);
            });
        }
    };
})();
