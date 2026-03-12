(function() {
    var ITEM_HEIGHT_EST = 32;
    var GAP = 4;
    var STAGGER_MS = 80;
    var REFRESH_MS = 2000;
    var POLL_INTERVAL_MS = 2000;

    function latLngToMaidenhead4(lat, lon) {
        if (lat == null || lon == null || isNaN(lat) || isNaN(lon)) return '';
        var lonNorm = (lon + 180) / 20;
        var latNorm = (lat + 90) / 10;
        var c1 = String.fromCharCode(65 + Math.min(17, Math.floor(lonNorm)));
        var c2 = String.fromCharCode(65 + Math.min(17, Math.floor(latNorm)));
        var c3 = Math.floor((lonNorm % 1) * 10);
        var c4 = Math.floor((latNorm % 1) * 10);
        return c1 + c2 + c3 + c4;
    }

    function formatLastSeen(ts) {
        if (ts == null || ts === '') return '';
        var now = Date.now() / 1000;
        var sec = now - ts;
        if (sec < 60) return Math.round(sec) + 's ago';
        if (sec < 3600) return Math.round(sec / 60) + 'm ago';
        if (sec < 86400) return Math.round(sec / 3600) + 'h ago';
        return Math.round(sec / 86400) + 'd ago';
    }

    function getCellSettings(cell) {
        var allSettings = window.GLANCERF_MODULE_SETTINGS || {};
        var r = cell.getAttribute('data-row');
        var c = cell.getAttribute('data-col');
        var cellKey = (r != null && c != null) ? r + '_' + c : '';
        return (cellKey && allSettings[cellKey]) ? allSettings[cellKey] : {};
    }

    function setState(cell, state) {
        cell.classList.remove('aprs_state_empty', 'aprs_state_loading', 'aprs_state_error');
        if (state) cell.classList.add('aprs_state_' + state);
    }

    function getMaxVisible(cell) {
        var listEl = cell.querySelector('.aprs_list');
        if (!listEl) return 12;
        var h = listEl.getBoundingClientRect().height;
        if (h <= 0) return 12;
        return Math.max(3, Math.floor(h / (ITEM_HEIGHT_EST + GAP)));
    }

    function locKey(loc) {
        return (loc.callsign || '').trim();
    }

    function createItemEl(loc, animate) {
        var item = document.createElement('div');
        item.className = 'aprs_item' + (animate ? ' aprs_item_entering' : '');
        var call = (loc.callsign || '').trim();
        var last = formatLastSeen(loc.lastSeen);
        var grid = latLngToMaidenhead4(loc.lat, loc.lon);
        item.innerHTML =
            '<span class="aprs_call">' + call + '</span> ' +
            '<span class="aprs_last">' + last + '</span>' +
            (grid ? ' <span class="aprs_grid">' + grid + '</span>' : '');
        return item;
    }

    function renderListImmediate(cell, locations, maxEntries, emptyEl, listEl) {
        cell.classList.remove('aprs_show_empty');
        if (!locations || locations.length === 0) {
            if (emptyEl) emptyEl.textContent = 'No APRS stations in time window.';
            setState(cell, 'empty');
            listEl.innerHTML = '';
            return;
        }
        setState(cell, '');
        var sorted = locations.slice().sort(function(a, b) {
            var ta = a.lastSeen || 0;
            var tb = b.lastSeen || 0;
            return tb - ta;
        });
        var maxVisible = Math.min(maxEntries, getMaxVisible(cell));
        var slice = sorted.slice(0, maxVisible);
        listEl.innerHTML = '';
        slice.forEach(function(loc) {
            listEl.appendChild(createItemEl(loc, false));
        });
    }

    function processBacklog(cell, backlog, listEl, maxVisible) {
        if (!backlog || backlog.length === 0) return;
        var idx = 0;
        function addNext() {
            if (idx >= backlog.length) return;
            var loc = backlog[idx++];
            var key = locKey(loc);
            var children = listEl.children;
            for (var i = 0; i < children.length; i++) {
                var c = children[i];
                var callEl = c.querySelector('.aprs_call');
                var ckey = callEl ? (callEl.textContent || '').trim() : '';
                if (ckey === key) {
                    listEl.removeChild(c);
                    break;
                }
            }
            var item = createItemEl(loc, true);
            listEl.insertBefore(item, listEl.firstChild);
            while (listEl.children.length > maxVisible) {
                var last = listEl.lastChild;
                if (last) listEl.removeChild(last);
            }
            setTimeout(addNext, STAGGER_MS);
        }
        addNext();
    }

    function updateCell(cell) {
        var listEl = cell.querySelector('.aprs_list');
        var emptyEl = cell.querySelector('.aprs_empty');
        var errorEl = cell.querySelector('.aprs_error');

        if (!listEl) return;

        var settings = getCellSettings(cell);
        var maxEntries = 30;
        try {
            var n = parseInt(settings.max_entries, 10);
            if (n > 0 && n <= 100) maxEntries = n;
        } catch (e) {}
        var hours = 6;
        try {
            var h = parseFloat(settings.hours, 10);
            if (h > 0 && h <= 168) hours = h;
        } catch (e) {}
        var filterStr = (settings.aprs_filter != null && typeof settings.aprs_filter === 'string') ? settings.aprs_filter.trim() : '';

        var hasContent = listEl && listEl.children.length > 0;
        var isBackgroundRefresh = cell.getAttribute('data-aprs-loaded') === '1' || hasContent;
        var prevData = cell._aprs_prev || { locations: [] };

        if (!isBackgroundRefresh) {
            if (emptyEl) emptyEl.textContent = 'Loading APRS stations...';
            cell.classList.add('aprs_show_empty');
        }

        var url = '/api/map/aprs-locations?hours=' + encodeURIComponent(hours);
        if (filterStr) url += '&filter=' + encodeURIComponent(filterStr);
        fetch(url)
            .then(function(r) { return r.json(); })
            .then(function(data) {
                if (errorEl) errorEl.textContent = '';
                if (data.error) {
                    cell.classList.remove('aprs_show_empty');
                    if (errorEl) errorEl.textContent = data.error;
                    setState(cell, 'error');
                    if (!isBackgroundRefresh) listEl.innerHTML = '';
                    return;
                }
                var locations = (data.locations && Array.isArray(data.locations)) ? data.locations : [];
                cell.classList.remove('aprs_show_empty');
                var maxVisible = Math.min(maxEntries, getMaxVisible(cell));

                var sorted = locations.slice().sort(function(a, b) {
                    return (b.lastSeen || 0) - (a.lastSeen || 0);
                });

                var backlog = [];
                var prevByKey = {};
                (prevData.locations || []).forEach(function(l) {
                    var k = locKey(l);
                    if (!prevByKey[k] || (l.lastSeen || 0) > (prevByKey[k].lastSeen || 0)) {
                        prevByKey[k] = l;
                    }
                });
                sorted.forEach(function(loc) {
                    var k = locKey(loc);
                    var prev = prevByKey[k];
                    var ts = loc.lastSeen || 0;
                    var prevTs = prev ? (prev.lastSeen || 0) : 0;
                    if (ts > prevTs) backlog.push(loc);
                });
                backlog.sort(function(a, b) { return (a.lastSeen || 0) - (b.lastSeen || 0); });

                if (backlog.length > 0 && hasContent) {
                    processBacklog(cell, backlog, listEl, maxVisible);
                } else {
                    renderListImmediate(cell, locations, maxEntries, emptyEl, listEl);
                }

                prevData.locations = sorted;
                cell._aprs_prev = prevData;
                cell.setAttribute('data-aprs-loaded', '1');
                cell.setAttribute('data-aprs-last-ts', String(Date.now()));
            })
            .catch(function() {
                cell.classList.remove('aprs_show_empty');
                if (!isBackgroundRefresh) {
                    setState(cell, 'error');
                    if (errorEl) errorEl.textContent = 'Failed to load APRS stations.';
                    listEl.innerHTML = '';
                }
            });
    }

    function run() {
        var now = Date.now();
        document.querySelectorAll('.grid-cell-aprs').forEach(function(cell) {
            var lastTs = parseInt(cell.getAttribute('data-aprs-last-ts') || '0', 10);
            if (lastTs === 0 || (now - lastTs) >= REFRESH_MS) {
                updateCell(cell);
            }
        });
    }

    document.addEventListener('glancerf_aprs_update', function() {
        document.querySelectorAll('.grid-cell-aprs').forEach(function(cell) {
            updateCell(cell);
        });
    });

    run();
    setInterval(run, POLL_INTERVAL_MS);
})();
