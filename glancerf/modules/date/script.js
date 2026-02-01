(function() {
    function scaleDateToCell() {
        document.querySelectorAll('.grid-cell-date').forEach(function(cell) {
            var display = cell.querySelector('.date_display');
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
        scaleDateToCell();
        requestAnimationFrame(function() { scaleDateToCell(); });
        setTimeout(scaleDateToCell, 150);
        setTimeout(scaleDateToCell, 450);
    }
    function formatDate(now, fmt) {
        var wd = now.toLocaleDateString('en-GB', { weekday: 'short' });
        var d = now.getDate();
        var mon = now.toLocaleDateString('en-GB', { month: 'short' });
        var y = now.getFullYear();
        if (fmt === 'mdy') return wd + ' ' + mon + ' ' + d + ', ' + y;
        if (fmt === 'ymd') return wd + ' ' + y + ' ' + mon + ' ' + d;
        return wd + ' ' + d + ' ' + mon + ' ' + y;
    }
    function updateDates() {
        var now = new Date();
        var allSettings = window.GLANCERF_MODULE_SETTINGS || {};
        document.querySelectorAll('.grid-cell-date').forEach(function(cell) {
            var r = cell.getAttribute('data-row');
            var c = cell.getAttribute('data-col');
            var cellKey = (r != null && c != null) ? r + '_' + c : '';
            var ms = (cellKey && allSettings[cellKey]) ? allSettings[cellKey] : {};
            var fmt = (ms.date_format || 'dmy').toLowerCase();
            var el = cell.querySelector('.date_value');
            if (el) el.textContent = formatDate(now, fmt);
        });
    }
    updateDates();
    setInterval(updateDates, 60000);
    runScaleWhenReady();
    window.addEventListener('load', runScaleWhenReady);
    window.addEventListener('resize', scaleDateToCell);
    if (typeof ResizeObserver !== 'undefined') {
        document.querySelectorAll('.grid-cell-date').forEach(function(cell) {
            var ro = new ResizeObserver(function() { scaleDateToCell(); });
            ro.observe(cell);
        });
        var checkNewDates = setInterval(function() {
            document.querySelectorAll('.grid-cell-date').forEach(function(cell) {
                if (!cell._dateResizeObserved) {
                    cell._dateResizeObserved = true;
                    var ro = new ResizeObserver(function() { scaleDateToCell(); });
                    ro.observe(cell);
                }
            });
        }, 500);
        setTimeout(function() { clearInterval(checkNewDates); }, 5000);
    }
})();
