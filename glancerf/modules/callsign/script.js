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
        });
    }
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
