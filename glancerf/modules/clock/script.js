(function() {
    function isOn(val) {
        return val === '1' || val === 1 || val === true || val === 'true';
    }
    function scaleClockToCell() {
        document.querySelectorAll('.grid-cell-clock').forEach(function(cell) {
            var display = cell.querySelector('.clock_display');
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
        scaleClockToCell();
        requestAnimationFrame(function() { scaleClockToCell(); });
        setTimeout(scaleClockToCell, 150);
        setTimeout(scaleClockToCell, 450);
    }
    function updateClocks() {
        var now = new Date();
        var localStr = now.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
        var utcStr = now.toUTCString().split(' ')[4];
        var allSettings = window.GLANCERF_MODULE_SETTINGS || {};
        document.querySelectorAll('.grid-cell-clock').forEach(function(cell) {
            var r = cell.getAttribute('data-row');
            var c = cell.getAttribute('data-col');
            var cellKey = (r != null && c != null) ? r + '_' + c : '';
            var ms = (cellKey && allSettings[cellKey]) ? allSettings[cellKey] : {};
            var showDate = ms.show_date !== undefined ? isOn(ms.show_date) : false;
            var showLocal = ms.show_local !== undefined ? isOn(ms.show_local) : true;
            var showUtc = ms.show_utc !== undefined ? isOn(ms.show_utc) : true;
            var thirdTz = ms.third_timezone || '';
            var dateEl = cell.querySelector('.clock_date');
            var localEl = cell.querySelector('.clock_local');
            var utcEl = cell.querySelector('.clock_utc');
            var thirdEl = cell.querySelector('.clock_third');
            if (dateEl) {
                dateEl.style.display = showDate ? '' : 'none';
                if (showDate) {
                    var wd = now.toLocaleDateString('en-GB', { weekday: 'short' });
                    var d = now.getDate();
                    var mon = now.toLocaleDateString('en-GB', { month: 'short' });
                    var y = now.getFullYear();
                    dateEl.textContent = wd + ' ' + d + ' ' + mon + ' ' + y;
                }
            }
            if (localEl) {
                localEl.textContent = 'Local ' + localStr;
                localEl.style.display = showLocal ? '' : 'none';
            }
            if (utcEl) {
                utcEl.textContent = 'UTC ' + utcStr;
                utcEl.style.display = showUtc ? '' : 'none';
            }
            var thirdVisible = false;
            if (thirdEl) {
                if (thirdTz) {
                    try {
                        var thirdStr = now.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false, timeZone: thirdTz });
                        thirdEl.textContent = thirdTz.replace(/_/g, ' ') + ' ' + thirdStr;
                        thirdEl.style.display = '';
                        thirdVisible = true;
                    } catch (e) {
                        thirdEl.style.display = 'none';
                    }
                } else {
                    thirdEl.style.display = 'none';
                }
            }
            var primaryEl = showLocal ? localEl : (showUtc ? utcEl : (thirdVisible ? thirdEl : null));
            [dateEl, localEl, utcEl, thirdEl].forEach(function(el) {
                if (el) {
                    if (el === primaryEl) el.classList.add('clock_primary');
                    else el.classList.remove('clock_primary');
                }
            });
        });
    }
    updateClocks();
    setInterval(updateClocks, 1000);
    runScaleWhenReady();
    window.addEventListener('load', runScaleWhenReady);
    window.addEventListener('resize', scaleClockToCell);
    if (typeof ResizeObserver !== 'undefined') {
        document.querySelectorAll('.grid-cell-clock').forEach(function(cell) {
            var ro = new ResizeObserver(function() { scaleClockToCell(); });
            ro.observe(cell);
        });
        var checkNewClocks = setInterval(function() {
            document.querySelectorAll('.grid-cell-clock').forEach(function(cell) {
                if (!cell._clockResizeObserved) {
                    cell._clockResizeObserved = true;
                    var ro = new ResizeObserver(function() { scaleClockToCell(); });
                    ro.observe(cell);
                }
            });
        }, 500);
        setTimeout(function() { clearInterval(checkNewClocks); }, 5000);
    }
})();
