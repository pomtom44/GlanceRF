(function() {
            function getSettings(containerEl) {
                var cell = containerEl.closest('.grid-cell-rss');
                if (!cell) return {};
                var allSettings = window.GLANCERF_MODULE_SETTINGS || {};
                var r = cell.getAttribute('data-row');
                var c = cell.getAttribute('data-col');
                var key = (r != null && c != null) ? r + '_' + c : '';
                return (key && allSettings[key]) ? allSettings[key] : {};
            }
            function parseNum(val, defaultVal, minVal, maxVal) {
                var n = parseInt(val, 10);
                if (isNaN(n)) return defaultVal;
                if (minVal != null && n < minVal) return minVal;
                if (maxVal != null && n > maxVal) return maxVal;
                return n;
            }
            function showLoading(cell, on) {
                var loadEl = cell.querySelector('.rss_loading');
                var errEl = cell.querySelector('.rss_error');
                var listEl = cell.querySelector('.rss_list');
                if (on) {
                    if (errEl) errEl.style.display = 'none';
                    if (loadEl) { loadEl.textContent = 'Loading...'; loadEl.style.display = ''; }
                    if (listEl) listEl.style.display = 'none';
                } else if (loadEl) loadEl.style.display = 'none';
            }
            function showError(cell, msg) {
                var errEl = cell.querySelector('.rss_error');
                var loadEl = cell.querySelector('.rss_loading');
                var listEl = cell.querySelector('.rss_list');
                if (loadEl) loadEl.style.display = 'none';
                if (listEl) listEl.style.display = 'none';
                if (errEl) { errEl.textContent = msg || 'Error'; errEl.style.display = ''; }
            }
            function showFeed(cell, data, maxItems) {
                var titleEl = cell.querySelector('.rss_title');
                var listEl = cell.querySelector('.rss_list');
                var errEl = cell.querySelector('.rss_error');
                var loadEl = cell.querySelector('.rss_loading');
                if (loadEl) loadEl.style.display = 'none';
                if (errEl) errEl.style.display = 'none';
                if (titleEl && data.title) {
                    titleEl.textContent = data.title;
                    titleEl.style.display = '';
                } else if (titleEl) titleEl.style.display = 'none';
                if (!listEl) return;
                listEl.style.display = '';
                listEl.innerHTML = '';
                var items = (data.items || []).slice(0, maxItems);
                items.forEach(function(item) {
                    var li = document.createElement('li');
                    var title = (item.title || '').trim() || '(No title)';
                    if (item.link) {
                        var a = document.createElement('a');
                        a.href = item.link;
                        a.target = '_blank';
                        a.rel = 'noopener noreferrer';
                        a.className = 'rss_item_title';
                        a.textContent = title;
                        li.appendChild(a);
                    } else {
                        var span = document.createElement('span');
                        span.className = 'rss_item_title';
                        span.textContent = title;
                        li.appendChild(span);
                    }
                    listEl.appendChild(li);
                });
            }
            function updateCell(cell, cellKey, ms, forceRefresh) {
                var url = (ms.rss_url || '').toString().trim();
                if (!url) {
                    showError(cell, 'Set RSS feed URL');
                    return;
                }
                var maxItems = parseNum(ms.max_items, 10, 1, 50);
                var refreshMin = parseNum(ms.refresh_min, 15, 1, 120);
                var refreshMs = refreshMin * 60 * 1000;
                var tsKey = 'rss_ts_' + cellKey;
                if (!forceRefresh && window[tsKey]) {
                    if (Date.now() - window[tsKey] < refreshMs) return;
                }
                showLoading(cell, true);
                var apiUrl = '/api/rss?url=' + encodeURIComponent(url);
                fetch(apiUrl).then(function(r) {
                    return r.json().then(function(data) {
                        return { ok: r.ok, status: r.status, data: data };
                    });
                }).then(function(result) {
                    showLoading(cell, false);
                    if (result.ok && result.data && !result.data.error) {
                        showFeed(cell, result.data, maxItems);
                        try { window[tsKey] = Date.now(); } catch (e) {}
                    } else {
                        var msg = (result.data && result.data.error) ? result.data.error : 'Feed unavailable';
                        if (result.data && result.data.detail) msg += ' (' + result.data.detail + ')';
                        showError(cell, msg);
                    }
                }).catch(function(err) {
                    showLoading(cell, false);
                    showError(cell, (err && err.message) ? err.message : 'Network error');
                });
            }
            function runAll() {
                var allSettings = window.GLANCERF_MODULE_SETTINGS || {};
                document.querySelectorAll('.grid-cell-rss').forEach(function(cell) {
                    var r = cell.getAttribute('data-row');
                    var c = cell.getAttribute('data-col');
                    var cellKey = (r != null && c != null) ? r + '_' + c : '';
                    var ms = (cellKey && allSettings[cellKey]) ? allSettings[cellKey] : {};
                    updateCell(cell, cellKey, ms, false);
                });
            }
            runAll();
            setInterval(runAll, 60 * 1000);
        })();
