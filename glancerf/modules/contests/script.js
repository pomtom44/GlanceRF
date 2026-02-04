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

    function getCellSettings(cell) {
        var allSettings = window.GLANCERF_MODULE_SETTINGS || {};
        var r = cell.getAttribute('data-row');
        var c = cell.getAttribute('data-col');
        var cellKey = (r != null && c != null) ? r + '_' + c : '';
        return (cellKey && allSettings[cellKey]) ? allSettings[cellKey] : {};
    }

    function setState(cell, state) {
        cell.classList.remove('contests_state_empty', 'contests_state_loading', 'contests_state_error');
        if (state) cell.classList.add('contests_state_' + state);
    }

    function updateCell(cell) {
        var listEl = cell.querySelector('.contests_list');
        var creditsEl = cell.querySelector('.contests_credits');
        var emptyEl = cell.querySelector('.contests_empty');
        var errorEl = cell.querySelector('.contests_error');

        if (!listEl) return;

        setState(cell, 'loading');
        if (emptyEl) emptyEl.textContent = 'Loading...';
        listEl.innerHTML = '';

        var settings = getCellSettings(cell);
        var maxEntries = 20;
        try {
            var n = parseInt(settings.max_entries, 10);
            if (n > 0 && n <= 100) maxEntries = n;
        } catch (e) {}
        var params = [];
        var enabledSources = settings.enabled_sources;
        if (enabledSources !== undefined && enabledSources !== null && enabledSources !== '') {
            var ids = typeof enabledSources === 'string' ? (function() {
                try { return JSON.parse(enabledSources); } catch (e) { return []; }
            }()) : (Array.isArray(enabledSources) ? enabledSources : []);
            params.push('sources=' + encodeURIComponent(ids.join(',')));
        }
        var customSources = settings.custom_sources;
        if (customSources !== undefined && customSources !== null && customSources !== '') {
            var customList = typeof customSources === 'string' ? (function() {
                try { return JSON.parse(customSources); } catch (e) { return []; }
            }()) : (Array.isArray(customSources) ? customSources : []);
            customList = customList.filter(function(c) { return c && (c.url || c.URL); });
            if (customList.length) params.push('custom_sources=' + encodeURIComponent(JSON.stringify(customList)));
        }
        var query = params.length ? '?' + params.join('&') : '';
        fetch('/api/contests/list' + query)
            .then(function(r) { return r.json(); })
            .then(function(data) {
                setState(cell, '');
                if (errorEl) errorEl.textContent = '';
                if (data.error) {
                    if (errorEl) errorEl.textContent = data.error;
                    setState(cell, 'error');
                    return;
                }
                var contests = (data.contests && Array.isArray(data.contests)) ? data.contests : [];
                var credits = data.credits || '';

                if (creditsEl) creditsEl.textContent = credits;

                if (contests.length === 0) {
                    if (emptyEl) emptyEl.textContent = 'No contests listed.';
                    setState(cell, 'empty');
                    listEl.innerHTML = '';
                    return;
                }

                listEl.innerHTML = '';
                var slice = contests.slice(0, maxEntries);
                slice.forEach(function(d) {
                    var item = document.createElement('div');
                    item.className = 'contests_item';
                    var title = (d.title || '').trim();
                    var url = (d.url || '').trim();
                    var dates = formatDateRange(d.start_utc, d.end_utc);
                    var info = (d.info || '').trim();
                    var source = (d.source || '').trim();
                    var titleHtml = url ? '<a href="' + url.replace(/"/g, '&quot;') + '" target="_blank" rel="noopener">' + title + '</a>' : title;
                    item.innerHTML =
                        '<span class="contests_name">' + titleHtml + '</span>' +
                        (source ? ' <span class="contests_source" title="Source">[' + source + ']</span>' : '') +
                        '<br><span class="contests_dates">' + dates + '</span>' +
                        (info ? '<br><span class="contests_info">' + info.substring(0, 80) + (info.length > 80 ? '...' : '') + '</span>' : '');
                    listEl.appendChild(item);
                });
            })
            .catch(function() {
                setState(cell, 'error');
                if (errorEl) errorEl.textContent = 'Failed to load contests.';
                listEl.innerHTML = '';
            });
    }

    function run() {
        document.querySelectorAll('.grid-cell-contests').forEach(function(cell) {
            updateCell(cell);
        });
    }

    run();
    setInterval(run, UPDATE_MS);
})();
