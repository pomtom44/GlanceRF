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

    function setLastRefresh(cell, date) {
        var el = cell.querySelector('.dxpeditions_last_refresh');
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

    function renderList(cell, dxpeds, credits, maxEntries, emptyEl, listEl, creditsEl) {
        if (creditsEl) creditsEl.textContent = credits || '';
        cell.classList.remove('dxpeditions_show_empty');
        if (!dxpeds || dxpeds.length === 0) {
            if (emptyEl) emptyEl.textContent = 'No DXpeditions listed.';
            setState(cell, 'empty');
            listEl.innerHTML = '';
            return;
        }
        setState(cell, '');
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
        listEl.scrollTop = 0;
    }

    function updateCell(cell) {
        var wrap = cell.querySelector('.dxpeditions_wrap');
        var listEl = cell.querySelector('.dxpeditions_list');
        var creditsEl = cell.querySelector('.dxpeditions_credits');
        var emptyEl = cell.querySelector('.dxpeditions_empty');
        var errorEl = cell.querySelector('.dxpeditions_error');

        if (!wrap || !listEl) return;

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

        var hasContent = listEl && listEl.children.length > 0;
        var isBackgroundRefresh = cell.getAttribute('data-dxpeditions-loaded') === '1' || hasContent;

        if (!isBackgroundRefresh) {
            if (emptyEl) emptyEl.textContent = 'Loading dxpeditions...';
            cell.classList.add('dxpeditions_show_empty');
        }

        fetch('/api/dxpeditions/list' + sourcesParam)
            .then(function(r) { return r.json(); })
            .then(function(data) {
                if (errorEl) errorEl.textContent = '';
                if (data.error) {
                    cell.classList.remove('dxpeditions_show_empty');
                    if (errorEl) errorEl.textContent = data.error;
                    setState(cell, 'error');
                    if (!isBackgroundRefresh) listEl.innerHTML = '';
                    return;
                }
                var dxpeds = (data.dxpeditions && Array.isArray(data.dxpeditions)) ? data.dxpeditions : [];
                var credits = data.credits || '';
                cell.classList.remove('dxpeditions_show_empty');
                renderList(cell, dxpeds, credits, maxEntries, emptyEl, listEl, creditsEl);
                cell.setAttribute('data-dxpeditions-loaded', '1');
                cell.setAttribute('data-dxpeditions-last-ts', String(Date.now()));
                setLastRefresh(cell, new Date());
            })
            .catch(function() {
                cell.classList.remove('dxpeditions_show_empty');
                if (!isBackgroundRefresh) {
                    setState(cell, 'error');
                    if (errorEl) errorEl.textContent = 'Failed to load DXpeditions.';
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
        document.querySelectorAll('.grid-cell-dxpeditions').forEach(function(cell) {
            var lastTs = parseInt(cell.getAttribute('data-dxpeditions-last-ts') || '0', 10);
            var refreshMs = getRefreshMs(cell);
            if (lastTs === 0 || (now - lastTs) >= refreshMs) {
                updateCell(cell);
            }
        });
    }

    var SCROLL_SPEED_PX_PER_SEC = 18;
    var SCROLL_WAIT_BOTTOM_MS = 4000;
    var SCROLL_WAIT_TOP_MS = 4000;

    function startAutoScroll(cell, listEl) {
        if (!listEl || !cell) return;
        var rafId = null;

        function smoothScrollTo(target, duration, done) {
            var start = listEl.scrollTop;
            var dist = target - start;
            var startTime = performance.now();
            function step(now) {
                var elapsed = now - startTime;
                var progress = Math.min(elapsed / duration, 1);
                var eased = progress < 0.5 ? 2 * progress * progress : 1 - Math.pow(-2 * progress + 2, 2) / 2;
                listEl.scrollTop = start + dist * eased;
                if (progress < 1) {
                    rafId = requestAnimationFrame(step);
                } else if (done) {
                    done();
                }
            }
            rafId = requestAnimationFrame(step);
        }

        function cycle() {
            if (cell.getAttribute('data-dxpeditions-scroll-off') === '1') return;
            var maxScroll = listEl.scrollHeight - listEl.clientHeight;
            if (maxScroll <= 0) {
                setTimeout(cycle, 2000);
                return;
            }
            var durationMs = (maxScroll / SCROLL_SPEED_PX_PER_SEC) * 1000;
            smoothScrollTo(maxScroll, durationMs, function() {
                if (cell.getAttribute('data-dxpeditions-scroll-off') === '1') return;
                setTimeout(function() {
                    if (cell.getAttribute('data-dxpeditions-scroll-off') === '1') return;
                    listEl.scrollTop = 0;
                    setTimeout(function() {
                        if (cell.getAttribute('data-dxpeditions-scroll-off') === '1') return;
                        cycle();
                    }, SCROLL_WAIT_TOP_MS);
                }, SCROLL_WAIT_BOTTOM_MS);
            });
        }
        cell.setAttribute('data-dxpeditions-scroll-off', '0');
        setTimeout(cycle, Math.random() * 6000);
    }

    function runScrollToggles() {
        document.querySelectorAll('.grid-cell-dxpeditions').forEach(function(cell) {
            var listEl = cell.querySelector('.dxpeditions_list');
            var settings = getCellSettings(cell);
            var enabled = !!(settings.scroll_toggle === true || settings.scroll_toggle === 'true' || settings.scroll_toggle === '1' || settings.scroll_toggle === 1);
            if (enabled) {
                cell.classList.add('dxpeditions_scroll_toggle');
                if (cell.getAttribute('data-dxpeditions-scroll-started') !== '1') {
                    cell.setAttribute('data-dxpeditions-scroll-started', '1');
                    startAutoScroll(cell, listEl);
                }
            } else {
                cell.classList.remove('dxpeditions_scroll_toggle');
                cell.setAttribute('data-dxpeditions-scroll-started', '0');
                cell.setAttribute('data-dxpeditions-scroll-off', '1');
            }
        });
    }

    run();
    runScrollToggles();
    setInterval(run, 25 * 1000);
    setInterval(runScrollToggles, 5000);
})();
