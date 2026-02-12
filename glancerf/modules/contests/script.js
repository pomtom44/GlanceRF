(function() {
    var DEFAULT_REFRESH_HOURS = 6;

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

    function setLastRefresh(cell, date) {
        var el = cell.querySelector('.contests_last_refresh');
        if (!el) return;
        if (!date) {
            el.textContent = '';
            el.style.display = 'none';
            return;
        }
        try {
            var d = date instanceof Date ? date : new Date(date);
            var day = d.getDate();
            var m = d.getMonth() + 1;
            var y = d.getFullYear();
            var h = d.getHours();
            var min = d.getMinutes();
            var t = String(h).padStart(2, '0') + ':' + String(min).padStart(2, '0');
            el.textContent = 'Last refreshed: ' + day + ' ' + ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][m - 1] + ' ' + t;
            el.style.display = '';
        } catch (e) {
            el.textContent = '';
            el.style.display = 'none';
        }
    }

    function renderList(cell, contests, credits, maxEntries, emptyEl, listEl, creditsEl) {
        if (creditsEl) creditsEl.textContent = credits || '';
        cell.classList.remove('contests_show_empty');
        if (!contests || contests.length === 0) {
            if (emptyEl) emptyEl.textContent = 'No contests listed.';
            setState(cell, 'empty');
            listEl.innerHTML = '';
            return;
        }
        setState(cell, '');
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
    }

    function updateCell(cell) {
        var listEl = cell.querySelector('.contests_list');
        var creditsEl = cell.querySelector('.contests_credits');
        var emptyEl = cell.querySelector('.contests_empty');
        var errorEl = cell.querySelector('.contests_error');

        if (!listEl) return;

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

        var hasContent = listEl && listEl.children.length > 0;
        var isBackgroundRefresh = cell.getAttribute('data-contests-loaded') === '1' || hasContent;

        if (!isBackgroundRefresh) {
            if (emptyEl) emptyEl.textContent = 'Loading contests...';
            cell.classList.add('contests_show_empty');
        }

        fetch('/api/contests/list' + query)
            .then(function(r) { return r.json(); })
            .then(function(data) {
                if (errorEl) errorEl.textContent = '';
                if (data.error) {
                    cell.classList.remove('contests_show_empty');
                    if (errorEl) errorEl.textContent = data.error;
                    setState(cell, 'error');
                    if (isBackgroundRefresh) return;
                    listEl.innerHTML = '';
                    return;
                }
                var contests = (data.contests && Array.isArray(data.contests)) ? data.contests : [];
                var credits = data.credits || '';
                cell.classList.remove('contests_show_empty');
                renderList(cell, contests, credits, maxEntries, emptyEl, listEl, creditsEl);
                cell.setAttribute('data-contests-loaded', '1');
                cell.setAttribute('data-contests-last-ts', String(Date.now()));
                setLastRefresh(cell, new Date());
            })
            .catch(function() {
                cell.classList.remove('contests_show_empty');
                if (!isBackgroundRefresh) {
                    setState(cell, 'error');
                    if (errorEl) errorEl.textContent = 'Failed to load contests.';
                    listEl.innerHTML = '';
                }
            });
    }

    function getRefreshMs(cell) {
        var settings = getCellSettings(cell);
        var refreshHours = DEFAULT_REFRESH_HOURS;
        try {
            var rh = parseFloat(settings.refresh_hours, 10);
            if (rh > 0 && rh <= 168) refreshHours = rh;
        } catch (e) {}
        return Math.max(60000, refreshHours * 60 * 60 * 1000);
    }

    function run() {
        var now = Date.now();
        document.querySelectorAll('.grid-cell-contests').forEach(function(cell) {
            var lastTs = parseInt(cell.getAttribute('data-contests-last-ts') || '0', 10);
            var refreshMs = getRefreshMs(cell);
            if (lastTs === 0 || (now - lastTs) >= refreshMs) {
                updateCell(cell);
            }
        });
    }

    run();
    setInterval(run, 25 * 1000);
})();
