(function() {
    function isOn(val) {
        return val === '1' || val === 1 || val === true || val === 'true';
    }
    function updateAnalogClocks() {
        var allSettings = window.GLANCERF_MODULE_SETTINGS || {};
        var cells = document.querySelectorAll('.grid-cell-analog_clock, .grid-cell-analog-clock');
        cells.forEach(function(cell) {
            var r = cell.getAttribute('data-row');
            var c = cell.getAttribute('data-col');
            var cellKey = (r != null && c != null) ? r + '_' + c : '';
            var ms = (cellKey && allSettings[cellKey]) ? allSettings[cellKey] : {};
            var showSeconds = ms.show_seconds !== undefined ? isOn(ms.show_seconds) : true;
            var tz = (ms.timezone || 'local').toLowerCase();
            var now = new Date();
            var hours, minutes, seconds;
            if (tz === 'utc') {
                hours = now.getUTCHours();
                minutes = now.getUTCMinutes();
                seconds = now.getUTCSeconds();
            } else {
                hours = now.getHours();
                minutes = now.getMinutes();
                seconds = now.getSeconds();
            }
            var hourAngle = (hours % 12) * 30 + minutes * 0.5 + seconds * (0.5 / 60);
            var minuteAngle = minutes * 6 + seconds * 0.1;
            var secondAngle = seconds * 6;
            var hourEl = cell.querySelector('.analog_clock_hour');
            var minuteEl = cell.querySelector('.analog_clock_minute');
            var secondEl = cell.querySelector('.analog_clock_second');
            if (hourEl) hourEl.setAttribute('transform', 'rotate(' + hourAngle + ' 50 50)');
            if (minuteEl) minuteEl.setAttribute('transform', 'rotate(' + minuteAngle + ' 50 50)');
            if (secondEl) {
                secondEl.setAttribute('transform', 'rotate(' + secondAngle + ' 50 50)');
                secondEl.style.display = showSeconds ? '' : 'none';
            }
        });
    }
    function startAnalogClocks() {
        updateAnalogClocks();
        setInterval(updateAnalogClocks, 1000);
    }
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', startAnalogClocks);
    } else {
        startAnalogClocks();
    }
})();
