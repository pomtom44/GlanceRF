(function() {
    function scaleCallsignToCell() {
        document.querySelectorAll('.grid-cell-callsign').forEach(function(cell) {
            var display = cell.querySelector('.callsign_display');
            if (!display) return;
            var w = cell.clientWidth;
            var h = cell.clientHeight;
            if (w <= 0 || h <= 0) return;
            var minDim = Math.min(w, h);
            var size = minDim * 0.16;
            size = Math.max(8, Math.min(80, size));
            display.style.fontSize = size + 'px';
        });
    }
    function runScaleWhenReady() {
        scaleCallsignToCell();
        requestAnimationFrame(function() { scaleCallsignToCell(); });
        setTimeout(scaleCallsignToCell, 150);
        setTimeout(scaleCallsignToCell, 450);
    }
    function updateCallsigns() {
        var allSettings = window.GLANCERF_MODULE_SETTINGS || {};
        document.querySelectorAll('.grid-cell-callsign').forEach(function(cell) {
            var r = cell.getAttribute('data-row');
            var c = cell.getAttribute('data-col');
            var cellKey = (r != null && c != null) ? r + '_' + c : '';
            var ms = (cellKey && allSettings[cellKey]) ? allSettings[cellKey] : {};
            var call = (ms.callsign || window.GLANCERF_SETUP_CALLSIGN || '').toString().trim();
            var grid = (ms.grid || window.GLANCERF_SETUP_LOCATION || '').toString().trim();
            var comment = (ms.comment || '').toString().trim();
            var callEl = cell.querySelector('.callsign_line');
            var gridEl = cell.querySelector('.callsign_grid');
            var commentEl = cell.querySelector('.callsign_comment');
            if (callEl) {
                callEl.textContent = call || 'Callsign';
                callEl.style.display = call ? '' : 'none';
            }
            if (gridEl) {
                gridEl.textContent = grid ? (grid.length <= 6 ? 'Grid: ' + grid.toUpperCase() : grid) : '';
                gridEl.style.display = grid ? '' : 'none';
            }
            if (commentEl) {
                commentEl.textContent = comment;
                commentEl.style.display = comment ? '' : 'none';
            }
            var otaEl = cell.querySelector('.callsign_on_the_air');
            if (otaEl) {
                otaEl.style.display = (window.GLANCERF_ON_THE_AIR ? '' : 'none');
            }
        });
    }
    function setOnTheAir(visible) {
        window.GLANCERF_ON_THE_AIR = !!visible;
        document.querySelectorAll('.grid-cell-callsign .callsign_on_the_air').forEach(function(el) {
            el.style.display = visible ? '' : 'none';
        });
        document.querySelectorAll('.grid-cell-on_the_air').forEach(function(cell) {
            var onEl = cell.querySelector('.on_the_air_text');
            var offEl = cell.querySelector('.on_the_air_off');
            if (onEl) onEl.style.display = visible ? '' : 'none';
            if (offEl) offEl.style.display = visible ? 'none' : '';
        });
    }
    window.addEventListener('glancerf_gpio_input', function(e) {
        var d = e.detail || {};
        if ((d.module_id === 'callsign' || d.module_id === 'on_the_air') && d.function_id === 'on_the_air') {
            setOnTheAir(d.value);
        }
    });
    window.addEventListener('glancerf_on_the_air', function(e) {
        setOnTheAir(e.detail != null ? e.detail.value : !window.GLANCERF_ON_THE_AIR);
    });
    if (window.GLANCERF_ON_THE_AIR === undefined) window.GLANCERF_ON_THE_AIR = false;
    updateCallsigns();
    runScaleWhenReady();
    window.addEventListener('load', runScaleWhenReady);
    window.addEventListener('resize', scaleCallsignToCell);
    if (typeof ResizeObserver !== 'undefined') {
        document.querySelectorAll('.grid-cell-callsign').forEach(function(cell) {
            var ro = new ResizeObserver(function() { scaleCallsignToCell(); });
            ro.observe(cell);
        });
        var checkNewCallsigns = setInterval(function() {
            document.querySelectorAll('.grid-cell-callsign').forEach(function(cell) {
                if (!cell._callsignResizeObserved) {
                    cell._callsignResizeObserved = true;
                    var ro = new ResizeObserver(function() { scaleCallsignToCell(); });
                    ro.observe(cell);
                }
            });
        }, 500);
        setTimeout(function() { clearInterval(checkNewCallsigns); }, 5000);
    }
})();
