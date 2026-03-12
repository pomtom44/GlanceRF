(function() {
    var liveStopwatchState = {};

    function parseDateOnly(s) {
        var m = (s || '').trim().match(/^(\d{4})-(\d{2})-(\d{2})$/);
        if (!m) return null;
        var y = parseInt(m[1], 10), mo = parseInt(m[2], 10) - 1, d = parseInt(m[3], 10);
        if (mo < 0 || mo > 11 || d < 1 || d > 31) return null;
        return new Date(y, mo, d);
    }
    function parseTime(s) {
        s = (s || '').trim();
        if (!s) return { h: 0, m: 0, s: 0 };
        var parts = s.split(':');
        var h = parseInt(parts[0], 10) || 0;
        var m = parts.length >= 2 ? (parseInt(parts[1], 10) || 0) : 0;
        var sec = parts.length >= 3 ? (parseInt(parts[2], 10) || 0) : 0;
        return { h: h, m: m, s: sec };
    }
    function parseDateTime(dateStr, timeStr) {
        var d = parseDateOnly(dateStr);
        if (!d) return null;
        var t = parseTime(timeStr);
        d.setHours(t.h, t.m, t.s, 0);
        return d.getTime();
    }
    function formatDuration(ms) {
        if (ms < 0) ms = 0;
        var sec = Math.floor(ms / 1000) % 60;
        var min = Math.floor(ms / 60000) % 60;
        var h = Math.floor(ms / 3600000) % 24;
        var d = Math.floor(ms / 86400000);
        var parts = [];
        if (d > 0) parts.push(d + 'd');
        parts.push(String(h).padStart(2, '0') + 'h');
        parts.push(String(min).padStart(2, '0') + 'm');
        parts.push(String(sec).padStart(2, '0') + 's');
        return parts.join(' ');
    }

    function getLiveElapsed(cellKey) {
        var s = liveStopwatchState[cellKey];
        if (!s) return 0;
        if (s.running && s.startTime != null) {
            return (s.pausedElapsed || 0) + (Date.now() - s.startTime);
        }
        return s.pausedElapsed || 0;
    }

    function doStartStop(cellKey) {
        var s = liveStopwatchState[cellKey] || { running: false, pausedElapsed: 0 };
        if (s.running) {
            s.pausedElapsed = (s.pausedElapsed || 0) + (Date.now() - (s.startTime || Date.now()));
            s.running = false;
            s.startTime = null;
        } else {
            s.startTime = Date.now();
            s.running = true;
        }
        liveStopwatchState[cellKey] = s;
    }

    function doReset(cellKey) {
        liveStopwatchState[cellKey] = { running: false, pausedElapsed: 0, startTime: null };
    }

    function updateCountdowns() {
        var now = Date.now();
        var allSettings = window.GLANCERF_MODULE_SETTINGS || {};
        document.querySelectorAll('.grid-cell-countdown').forEach(function(cell) {
            var r = cell.getAttribute('data-row');
            var c = cell.getAttribute('data-col');
            var cellKey = (r != null && c != null) ? r + '_' + c : '';
            var ms = (cellKey && allSettings[cellKey]) ? allSettings[cellKey] : {};
            var mode = (ms.mode || 'countdown').toLowerCase();
            var dateStr = (ms.date || '').toString().trim();
            var timeStr = (ms.time || '').toString().trim();
            var label = (ms.label || '').toString().trim();
            var valueEl = cell.querySelector('.countdown_value');
            var labelEl = cell.querySelector('.countdown_label');
            var msgEl = cell.querySelector('.countdown_message');
            if (labelEl) {
                labelEl.textContent = label;
                labelEl.style.display = label ? '' : 'none';
            }
            if (!valueEl) return;

            if (mode === 'live_stopwatch') {
                var elapsed = getLiveElapsed(cellKey);
                valueEl.textContent = formatDuration(elapsed);
                valueEl.style.display = '';
                if (msgEl) msgEl.style.display = 'none';
                return;
            }

            var ts = parseDateTime(dateStr, timeStr);
            if (!ts) {
                valueEl.textContent = mode === 'countdown' ? 'Set target date' : 'Set start date';
                valueEl.style.display = '';
                if (msgEl) msgEl.style.display = 'none';
                return;
            }
            if (mode === 'countdown') {
                var remaining = ts - now;
                if (remaining > 0) {
                    valueEl.textContent = formatDuration(remaining);
                    valueEl.style.display = '';
                    if (msgEl) { msgEl.style.display = 'none'; }
                } else {
                    valueEl.style.display = 'none';
                    if (msgEl) {
                        msgEl.textContent = label || 'Expired';
                        msgEl.style.display = '';
                    }
                }
            } else {
                var elapsed = now - ts;
                valueEl.textContent = formatDuration(elapsed);
                valueEl.style.display = '';
                if (msgEl) msgEl.style.display = 'none';
            }
        });
    }

    window.addEventListener('glancerf_gpio_input', function(e) {
        var d = e.detail || {};
        if (d.module_id !== 'countdown') return;
        var allSettings = window.GLANCERF_MODULE_SETTINGS || {};
        document.querySelectorAll('.grid-cell-countdown').forEach(function(cell) {
            var r = cell.getAttribute('data-row');
            var c = cell.getAttribute('data-col');
            var cellKey = (r != null && c != null) ? r + '_' + c : '';
            var ms = (cellKey && allSettings[cellKey]) ? allSettings[cellKey] : {};
            if ((ms.mode || '').toLowerCase() !== 'live_stopwatch') return;
            if (d.function_id === 'start_stop') {
                doStartStop(cellKey);
            } else if (d.function_id === 'reset') {
                doReset(cellKey);
            }
        });
    });

    document.addEventListener('keydown', function(e) {
        var active = document.activeElement;
        var isInput = active && (active.tagName === 'INPUT' || active.tagName === 'TEXTAREA' || active.tagName === 'SELECT' || active.isContentEditable);
        if (isInput) return;
        var key = e.key;
        var keyNorm = (key === ' ') ? ' ' : (key || '').toLowerCase();
        var allSettings = window.GLANCERF_MODULE_SETTINGS || {};
        document.querySelectorAll('.grid-cell-countdown').forEach(function(cell) {
            var r = cell.getAttribute('data-row');
            var c = cell.getAttribute('data-col');
            var cellKey = (r != null && c != null) ? r + '_' + c : '';
            var ms = (cellKey && allSettings[cellKey]) ? allSettings[cellKey] : {};
            if ((ms.mode || '').toLowerCase() !== 'live_stopwatch') return;
            var startStop = (ms.start_stop_shortcut || '').toString().trim();
            var reset = (ms.reset_shortcut || '').toString().trim();
            var startStopNorm = (startStop === ' ' || startStop.toLowerCase() === 'space') ? ' ' : startStop.toLowerCase();
            var resetNorm = (reset === ' ' || reset.toLowerCase() === 'space') ? ' ' : reset.toLowerCase();
            if (startStopNorm && keyNorm === startStopNorm) {
                e.preventDefault();
                doStartStop(cellKey);
            } else if (resetNorm && keyNorm === resetNorm) {
                e.preventDefault();
                doReset(cellKey);
            }
        });
    });

    updateCountdowns();
    setInterval(updateCountdowns, 1000);
})();
