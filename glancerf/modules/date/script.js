(function() {
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
})();
