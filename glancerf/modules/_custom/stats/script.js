(function() {
    var CACHE_MS = 5 * 60 * 1000;
    var cache = { ts: 0, data: null };

    function getCellKey(cell) {
        var r = cell.getAttribute('data-row');
        var c = cell.getAttribute('data-col');
        return (r != null && c != null) ? r + '_' + c : '';
    }

    function setState(cell, state) {
        cell.classList.remove('stats_state_loading', 'stats_state_error');
        if (state) cell.classList.add('stats_state_' + state);
    }

    function fmt(n) { return n != null ? String(n) : '—'; }

    function setBreakdowns(cell, data) {
        var countriesVal = cell.querySelector('.stats_countries_value');
        var countriesList = cell.querySelector('.stats_countries_list');
        var versionsList = cell.querySelector('.stats_versions_list');
        var platformsList = cell.querySelector('.stats_platforms_list');
        if (countriesVal) countriesVal.textContent = fmt(data.countries_seen);
        if (countriesList) {
            var countries = data.countries || [];
            countriesList.innerHTML = countries.slice(0, 4).map(function(c) {
                var name = (c.name || c.code || '').substring(0, 18);
                return '<div class="stats_breakdown_row"><span>' + escapeHtml(name) + '</span><span>' + (c.count != null ? c.count : '—') + '</span></div>';
            }).join('');
        }
        if (versionsList) {
            var vers = data.version_breakdown || [];
            versionsList.innerHTML = vers.slice(0, 4).map(function(v) {
                return '<div class="stats_breakdown_row"><span>' + escapeHtml(String(v.version || '—')) + '</span><span>' + (v.count != null ? v.count : '—') + '</span></div>';
            }).join('');
        }
        if (platformsList) {
            var plat = data.platform_breakdown || [];
            platformsList.innerHTML = plat.slice(0, 4).map(function(p) {
                return '<div class="stats_breakdown_row"><span>' + escapeHtml(String(p.platform || '—')) + '</span><span>' + (p.count != null ? p.count : '—') + '</span></div>';
            }).join('');
        }
    }

    function escapeHtml(s) {
        var div = document.createElement('div');
        div.textContent = s;
        return div.innerHTML;
    }

    function clearBreakdowns(cell) {
        var countriesVal = cell.querySelector('.stats_countries_value');
        var countriesList = cell.querySelector('.stats_countries_list');
        var versionsList = cell.querySelector('.stats_versions_list');
        var platformsList = cell.querySelector('.stats_platforms_list');
        if (countriesVal) countriesVal.textContent = '—';
        if (countriesList) countriesList.innerHTML = '';
        if (versionsList) versionsList.innerHTML = '';
        if (platformsList) platformsList.innerHTML = '';
    }

    function updateCell(cell) {
        var wrap = cell.querySelector('.stats_wrap');
        var valueEl = cell.querySelector('.stats_total_installs_value');
        var seenEl = cell.querySelector('.stats_seen_value');
        var errorEl = cell.querySelector('.stats_error');
        var loadingEl = cell.querySelector('.stats_loading');
        if (!wrap || !valueEl) return;

        if (cache.ts && (Date.now() - cache.ts) < CACHE_MS && cache.data !== null) {
            if (cache.data.error) {
                setState(cell, 'error');
                if (errorEl) errorEl.textContent = cache.data.error;
                valueEl.textContent = '—';
                if (seenEl) seenEl.textContent = '— / — / —';
                clearBreakdowns(cell);
            } else {
                setState(cell, '');
                valueEl.textContent = fmt(cache.data.total_installs);
                if (seenEl) seenEl.textContent = fmt(cache.data.seen_24h) + ' / ' + fmt(cache.data.seen_7d) + ' / ' + fmt(cache.data.seen_30d);
                if (errorEl) errorEl.textContent = '';
                setBreakdowns(cell, cache.data);
            }
            if (loadingEl) loadingEl.style.display = 'none';
            return;
        }

        setState(cell, 'loading');
        if (loadingEl) loadingEl.style.display = 'block';
        if (errorEl) errorEl.textContent = '';
        valueEl.textContent = '—';
        if (seenEl) seenEl.textContent = '— / — / —';
        clearBreakdowns(cell);

        fetch('/api/stats/installs')
            .then(function(r) { return r.json(); })
            .then(function(data) {
                cache.ts = Date.now();
                cache.data = data;
                if (data.error) {
                    setState(cell, 'error');
                    if (errorEl) errorEl.textContent = data.error;
                    valueEl.textContent = '—';
                    if (seenEl) seenEl.textContent = '— / — / —';
                    clearBreakdowns(cell);
                } else {
                    setState(cell, '');
                    valueEl.textContent = fmt(data.total_installs);
                    if (seenEl) seenEl.textContent = fmt(data.seen_24h) + ' / ' + fmt(data.seen_7d) + ' / ' + fmt(data.seen_30d);
                    if (errorEl) errorEl.textContent = '';
                    setBreakdowns(cell, data);
                }
                if (loadingEl) loadingEl.style.display = 'none';
            })
            .catch(function() {
                setState(cell, 'error');
                if (errorEl) errorEl.textContent = 'Failed to load stats';
                valueEl.textContent = '—';
                if (seenEl) seenEl.textContent = '— / — / —';
                clearBreakdowns(cell);
                if (loadingEl) loadingEl.style.display = 'none';
                cache.ts = 0;
            });
    }

    function run() {
        document.querySelectorAll('.grid-cell-stats').forEach(updateCell);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', run);
    } else {
        run();
    }
    setInterval(run, CACHE_MS);
})();
