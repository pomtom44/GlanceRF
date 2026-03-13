(function() {
    var GPS_UPDATE_MS = 2000;

    function formatCoord(lat, lon) {
        var ns = lat >= 0 ? 'N' : 'S';
        var ew = lon >= 0 ? 'E' : 'W';
        return Math.abs(lat).toFixed(4) + ns + ' ' + Math.abs(lon).toFixed(4) + ew;
    }

    function showLoading(cell, on) {
        var loadEl = cell.querySelector('.gps_loading');
        var discEl = cell.querySelector('.gps_disconnected');
        if (on) {
            if (loadEl) { loadEl.style.display = ''; loadEl.textContent = 'Checking GPS...'; }
            if (discEl) discEl.style.display = 'none';
        } else if (loadEl) {
            loadEl.style.display = 'none';
        }
    }

    function showDisconnected(cell) {
        var loadEl = cell.querySelector('.gps_loading');
        var discEl = cell.querySelector('.gps_disconnected');
        var posEl = cell.querySelector('.gps_position');
        var timeEl = cell.querySelector('.gps_time');
        var altEl = cell.querySelector('.gps_altitude');
        var speedEl = cell.querySelector('.gps_speed');
        var trackEl = cell.querySelector('.gps_track');
        var satsEl = cell.querySelector('.gps_satellites');
        if (loadEl) loadEl.style.display = 'none';
        if (discEl) { discEl.style.display = ''; discEl.textContent = 'No GPS connected'; }
        if (posEl) posEl.style.display = 'none';
        if (timeEl) timeEl.style.display = 'none';
        if (altEl) altEl.style.display = 'none';
        if (speedEl) speedEl.style.display = 'none';
        if (trackEl) trackEl.style.display = 'none';
        if (satsEl) satsEl.style.display = 'none';
    }

    function showStats(cell, data) {
        var loadEl = cell.querySelector('.gps_loading');
        var discEl = cell.querySelector('.gps_disconnected');
        var posEl = cell.querySelector('.gps_position');
        var timeEl = cell.querySelector('.gps_time');
        var altEl = cell.querySelector('.gps_altitude');
        var speedEl = cell.querySelector('.gps_speed');
        var trackEl = cell.querySelector('.gps_track');
        var satsEl = cell.querySelector('.gps_satellites');
        if (loadEl) loadEl.style.display = 'none';
        if (discEl) discEl.style.display = 'none';
        if (posEl) {
            posEl.textContent = formatCoord(data.lat, data.lon);
            posEl.style.display = '';
        }
        if (timeEl && (data.time_utc || data.date_utc)) {
            timeEl.textContent = (data.date_utc || '') + ' ' + (data.time_utc || '');
            timeEl.style.display = '';
        } else if (timeEl) timeEl.style.display = 'none';
        if (altEl && data.altitude_m != null) {
            altEl.textContent = 'Alt ' + data.altitude_m + ' m';
            altEl.style.display = '';
        } else if (altEl) altEl.style.display = 'none';
        if (speedEl && (data.speed_kmh != null || data.speed_ms != null)) {
            speedEl.textContent = 'Speed ' + (data.speed_kmh != null ? data.speed_kmh + ' km/h' : data.speed_ms + ' m/s');
            speedEl.style.display = '';
        } else if (speedEl) speedEl.style.display = 'none';
        if (trackEl && data.track_deg != null) {
            trackEl.textContent = 'Track ' + data.track_deg + '\u00B0';
            trackEl.style.display = '';
        } else if (trackEl) trackEl.style.display = 'none';
        if (satsEl && data.satellites != null) {
            satsEl.textContent = data.satellites + ' satellites';
            satsEl.style.display = '';
        } else if (satsEl) satsEl.style.display = 'none';
    }

    function updateCell(cell) {
        showLoading(cell, true);
        fetch('/api/gps/stats')
            .then(function(r) { return r.json(); })
            .then(function(data) {
                showLoading(cell, false);
                if (data && data.connected) {
                    showStats(cell, data);
                } else {
                    showDisconnected(cell);
                }
            })
            .catch(function() {
                showLoading(cell, false);
                showDisconnected(cell);
            });
    }

    function runAll() {
        document.querySelectorAll('.grid-cell-gps').forEach(function(cell) {
            updateCell(cell);
        });
    }

    runAll();
    setInterval(runAll, GPS_UPDATE_MS);
})();
