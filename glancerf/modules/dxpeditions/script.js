(function() {
    var UPDATE_MS = 300000;  // 5 minutes

    function formatDateRange(startUtc, endUtc) {
        if (!startUtc || !endUtc) return '';
        try {
            var s = startUtc.replace('Z', '');
            var e = endUtc.replace('Z', '');
            var ds = new Date(s);
            var de = new Date(e);
            var fmt = function(d) {
                var m = d.getUTCMonth() + 1;
                var day = d.getUTCDate();
                var y = d.getUTCFullYear();
                return day + '/' + m + '/' + y;
            };
            return fmt(ds) + ' - ' + fmt(de);
        } catch (err) {
            return startUtc + ' - ' + endUtc;
        }
    }

    function escapeHtml(s) {
        if (!s) return '';
        return String(s)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    }

    function getCellSettings(cell) {
        var allSettings = window.GLANCERF_MODULE_SETTINGS || {};
        var r = cell.getAttribute('data-row');
        var c = cell.getAttribute('data-col');
        var cellKey = (r != null && c != null) ? r + '_' + c : '';
        return (cellKey && allSettings[cellKey]) ? allSettings[cellKey] : {};
    }

    function setState(cell, state) {
        cell.classList.remove('dxpeditions_state_empty', 'dxpeditions_state_loading', 'dxpeditions_state_error');
        if (state) cell.classList.add('dxpeditions_state_' + state);
    }

    function updateCell(cell) {
        var wrap = cell.querySelector('.dxpeditions_wrap');
        var listEl = cell.querySelector('.dxpeditions_list');
        var creditsEl = cell.querySelector('.dxpeditions_credits');
        var emptyEl = cell.querySelector('.dxpeditions_empty');
        var errorEl = cell.querySelector('.dxpeditions_error');

        if (!wrap || !listEl) return;

        setState(cell, 'loading');
        if (emptyEl) emptyEl.textContent = 'Loading...';
        if (listEl) listEl.innerHTML = '';

        var settings = getCellSettings(cell);
        var maxEntries = 15;
        try {
            var n = parseInt(settings.max_entries, 10);
            if (n > 0 && n <= 50) maxEntries = n;
        } catch (e) {}
        var sourcesParam = '';
        var validDxSources = ['NG3K', 'NG3K RSS', 'DXCAL'];
        var enabledSources = settings.enabled_sources;
        if (enabledSources !== undefined && enabledSources !== null && enabledSources !== '') {
            var ids = typeof enabledSources === 'string' ? (function() {
                try { return JSON.parse(enabledSources); } catch (e) { return []; }
            }()) : (Array.isArray(enabledSources) ? enabledSources : []);
            var allowed = ids.filter(function(id) { return validDxSources.indexOf(id) >= 0; });
            if (allowed.length > 0) {
                sourcesParam = '?sources=' + encodeURIComponent(allowed.join(','));
            }
        }
        fetch('/api/dxpeditions/list' + sourcesParam)
            .then(function(r) { return r.json(); })
            .then(function(data) {
                setState(cell, '');
                if (errorEl) errorEl.textContent = '';
                if (data.error) {
                    if (errorEl) errorEl.textContent = data.error;
                    setState(cell, 'error');
                    if (emptyEl) emptyEl.style.display = 'none';
                    return;
                }
                var dxpeds = (data.dxpeditions && Array.isArray(data.dxpeditions)) ? data.dxpeditions : [];
                var credits = data.credits || '';

                if (creditsEl) creditsEl.textContent = credits;

                if (dxpeds.length === 0) {
                    if (emptyEl) emptyEl.textContent = 'No DXpeditions listed.';
                    setState(cell, 'empty');
                    listEl.innerHTML = '';
                    return;
                }

                listEl.innerHTML = '';
                var slice = dxpeds.slice(0, maxEntries);
                slice.forEach(function(d) {
                    var item = document.createElement('div');
                    item.className = 'dxpeditions_item';
                    var call = (d.call || '').trim();
                    var url = (d.url || '').trim();
                    var loc = (d.location || '').trim();
                    var dates = formatDateRange(d.start_utc, d.end_utc);
                    var info = (d.info || '').trim();
                    var source = (d.source || '').trim();
                    var callHtml = url ? '<a href="' + url.replace(/"/g, '&quot;') + '" target="_blank" rel="noopener">' + call + '</a>' : call;
                    item.innerHTML =
                        '<span class="dxpeditions_call">' + callHtml + '</span>' +
                        (loc ? ' <span class="dxpeditions_location">' + loc + '</span>' : '') +
                        (source ? ' <span class="dxpeditions_source" title="Source">[' + source + ']</span>' : '') +
                        '<br><span class="dxpeditions_dates">' + dates + '</span>' +
                        (info ? '<br><span class="dxpeditions_info">' + escapeHtml(info) + '</span>' : '');
                    listEl.appendChild(item);
                });
            })
            .catch(function() {
                setState(cell, 'error');
                if (errorEl) errorEl.textContent = 'Failed to load DXpeditions.';
                listEl.innerHTML = '';
            });
    }

    function run() {
        document.querySelectorAll('.grid-cell-dxpeditions').forEach(function(cell) {
            updateCell(cell);
        });
    }

    run();
    setInterval(run, UPDATE_MS);
})();
