(function() {
    var passListCountdownTimerId = null;

    function getMapApiBase() {
        var el = document.querySelector('[data-glancerf-base]');
        if (el && el.getAttribute('data-glancerf-base')) return el.getAttribute('data-glancerf-base').replace(/\/$/, '');
        return '';
    }

    function getCellSettings(cell) {
        var row = cell.getAttribute('data-row');
        var col = cell.getAttribute('data-col');
        var cellKey = (row != null && col != null) ? row + '_' + col : '';
        var moduleSettings = (typeof window.GLANCERF_MODULE_SETTINGS === 'object' && window.GLANCERF_MODULE_SETTINGS) || {};
        return cellKey ? (moduleSettings[cellKey] || {}) : {};
    }

    function getNextPassUrl(cell) {
        var base = getMapApiBase();
        var url = base + '/api/satellite/next_pass';
        var cellSettings = getCellSettings(cell);
        var location = (cellSettings.pass_location || '').trim() || (typeof window.GLANCERF_SETUP_LOCATION === 'string' ? (window.GLANCERF_SETUP_LOCATION || '').trim() : '');
        if (location) url += '?location=' + encodeURIComponent(location);
        return url;
    }

    function escapeHtml(s) {
        if (!s) return '';
        return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }

    function formatCountdown(utcStr) {
        if (!utcStr) return '';
        var t = new Date(utcStr).getTime();
        var now = Date.now();
        var ms = t - now;
        if (ms < 0) return '';
        var s = Math.floor(ms / 1000);
        var m = Math.floor(s / 60);
        var h = Math.floor(m / 60);
        s = s % 60;
        m = m % 60;
        if (h > 0) return 'In ' + h + 'h ' + (m < 10 ? '0' : '') + m + 'm';
        if (m > 0) return 'In ' + m + 'm ' + (s < 10 ? '0' : '') + s + 's';
        return 'In ' + s + 's';
    }

    function updateCompassView(cell, data) {
        var loadingEl = cell.querySelector('.sat_pass_compass_loading');
        var innerEl = cell.querySelector('.sat_pass_compass_inner');
        var errorEl = cell.querySelector('.sat_pass_compass_error');
        if (loadingEl) loadingEl.style.display = 'none';
        if (errorEl) errorEl.style.display = 'none';
        if (!data || !data.passes) {
            if (innerEl) innerEl.style.display = 'none';
            if (errorEl) {
                errorEl.style.display = 'flex';
                errorEl.textContent = data && data.text ? 'No future passes in cached window.' : 'No pass data.';
            }
            return;
        }
        var next = data.next_pass;
        var passes = data.passes || [];
        if (!next && passes.length === 0) {
            if (innerEl) innerEl.style.display = 'none';
            if (errorEl) {
                errorEl.style.display = 'flex';
                errorEl.textContent = 'No future passes in cached window.';
            }
            return;
        }
        if (innerEl) innerEl.style.display = 'flex';
    }

    function updatePassView(cell, data) {
        var loadingEl = cell.querySelector('.sat_pass_panel_loading');
        var bodyEl = cell.querySelector('.sat_pass_panel_body');
        var errorEl = cell.querySelector('.sat_pass_panel_error');
        var primaryEl = cell.querySelector('.sat_pass_primary');
        var countdownEl = cell.querySelector('.sat_pass_countdown');
        var secondaryEl = cell.querySelector('.sat_pass_secondary');
        var tbody = cell.querySelector('.sat_pass_upcoming_body');
        if (loadingEl) loadingEl.style.display = 'none';
        if (errorEl) errorEl.style.display = 'none';
        if (!data || !data.passes) {
            if (bodyEl) bodyEl.style.display = 'none';
            if (errorEl) {
                errorEl.style.display = 'flex';
                errorEl.textContent = data && data.text ? 'No future passes in cached window.' : 'No pass data.';
            }
            return;
        }
        var next = data.next_pass;
        var passes = data.passes || [];
        if (!next && passes.length === 0) {
            if (bodyEl) bodyEl.style.display = 'none';
            if (errorEl) {
                errorEl.style.display = 'flex';
                errorEl.textContent = 'No future passes in cached window.';
            }
            return;
        }
        if (bodyEl) bodyEl.style.display = 'flex';
        if (primaryEl) primaryEl.textContent = next ? (next.utc || '') : (passes[0] && passes[0].utc) || '';
        if (passListCountdownTimerId !== null) {
            clearInterval(passListCountdownTimerId);
            passListCountdownTimerId = null;
        }
        if (countdownEl) {
            var nextUtc = next && next.utc ? next.utc : '';
            countdownEl.textContent = nextUtc ? formatCountdown(nextUtc) : '';
            if (nextUtc) {
                passListCountdownTimerId = setInterval(function() {
                    var el = document.querySelector('.grid-cell-satellite_pass .sat_pass_countdown');
                    if (!el) return;
                    var text = formatCountdown(nextUtc);
                    el.textContent = text;
                    if (!text && passListCountdownTimerId !== null) {
                        clearInterval(passListCountdownTimerId);
                        passListCountdownTimerId = null;
                    }
                }, 1000);
            }
        }
        if (secondaryEl) {
            if (next) {
                secondaryEl.innerHTML = '<span class="sat_pass_name">' + escapeHtml(next.name || '') + '</span> NORAD ' + (next.norad || '') + ' &bull; ' + (next.km != null ? next.km + ' km' : '');
            } else if (passes[0]) {
                var p = passes[0];
                secondaryEl.innerHTML = '<span class="sat_pass_name">' + escapeHtml(p.name || '') + '</span> NORAD ' + (p.norad || '') + ' &bull; ' + (p.km != null ? p.km + ' km' : '');
            } else {
                secondaryEl.textContent = '';
            }
        }
        if (tbody) {
            tbody.innerHTML = '';
            var limit = 20;
            for (var i = 0; i < passes.length && i < limit; i++) {
                var p = passes[i];
                var tr = document.createElement('tr');
                tr.innerHTML = '<td>' + escapeHtml(p.utc || '') + '</td><td class="sat_pass_upcoming_name">' + escapeHtml((p.name || '').substring(0, 28)) + '</td><td>' + (p.km != null ? p.km : '') + '</td>';
                tbody.appendChild(tr);
            }
        }
    }

    function fetchNextPass() {
        var cell = document.querySelector('.grid-cell-satellite_pass');
        if (!cell) return;
        var cellSettings = getCellSettings(cell);
        var view = (cellSettings.sat_view || 'pass').toLowerCase();
        var isPass = (view !== 'list');

        var viewPass = cell.querySelector('.sat_pass_view_pass');
        var viewList = cell.querySelector('.sat_pass_view_list');
        if (viewPass) viewPass.style.display = isPass ? 'flex' : 'none';
        if (viewList) viewList.style.display = isPass ? 'none' : 'flex';

        if (!isPass && passListCountdownTimerId !== null) {
            clearInterval(passListCountdownTimerId);
            passListCountdownTimerId = null;
        }

        if (isPass) {
            var loadingEl = cell.querySelector('.sat_pass_compass_loading');
            var innerEl = cell.querySelector('.sat_pass_compass_inner');
            var errorEl = cell.querySelector('.sat_pass_compass_error');
            if (loadingEl) { loadingEl.style.display = 'flex'; loadingEl.textContent = 'Loading...'; }
            if (innerEl) innerEl.style.display = 'none';
            if (errorEl) errorEl.style.display = 'none';
            fetch(getNextPassUrl(cell)).then(function(r) { return r.json(); }).then(function(data) {
                updateCompassView(cell, data);
            }).catch(function() {
                if (loadingEl) loadingEl.style.display = 'none';
                if (innerEl) innerEl.style.display = 'none';
                if (errorEl) { errorEl.style.display = 'flex'; errorEl.textContent = 'Failed to load next pass.'; }
            });
            return;
        }

        var loadingEl = cell.querySelector('.sat_pass_panel_loading');
        var bodyEl = cell.querySelector('.sat_pass_panel_body');
        var errorEl = cell.querySelector('.sat_pass_panel_error');
        if (loadingEl) { loadingEl.style.display = 'flex'; loadingEl.textContent = 'Loading...'; }
        if (bodyEl) bodyEl.style.display = 'none';
        if (errorEl) errorEl.style.display = 'none';
        fetch(getNextPassUrl(cell)).then(function(r) { return r.json(); }).then(function(data) {
            updatePassView(cell, data);
        }).catch(function() {
            if (loadingEl) loadingEl.style.display = 'none';
            if (bodyEl) bodyEl.style.display = 'none';
            if (errorEl) { errorEl.style.display = 'flex'; errorEl.textContent = 'Failed to load passes.'; }
        });
    }

    function scheduleRefresh() {
        var cell = document.querySelector('.grid-cell-satellite_pass');
        if (!cell) return;
        fetchNextPass();
        setInterval(fetchNextPass, 60000);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', scheduleRefresh);
    } else {
        scheduleRefresh();
    }
})();
