(function() {
    var REFRESH_MS = 5 * 60 * 1000;
    var BANDS = [
        { id: '160', name: '160', minKHz: 1800, maxKHz: 2000 },
        { id: '80', name: '80', minKHz: 3500, maxKHz: 4000 },
        { id: '60', name: '60', minKHz: 5300, maxKHz: 5400 },
        { id: '40', name: '40', minKHz: 7000, maxKHz: 7300 },
        { id: '30', name: '30', minKHz: 10100, maxKHz: 10150 },
        { id: '20', name: '20', minKHz: 14000, maxKHz: 14350 },
        { id: '17', name: '17', minKHz: 18068, maxKHz: 18168 },
        { id: '15', name: '15', minKHz: 21000, maxKHz: 21450 },
        { id: '12', name: '12', minKHz: 24890, maxKHz: 24990 },
        { id: '10', name: '10', minKHz: 28000, maxKHz: 29700 },
        { id: '6', name: '6', minKHz: 50000, maxKHz: 54000 },
        { id: '2', name: '2', minKHz: 144000, maxKHz: 148000 }
    ];
    var DEFAULT_BAND_COLORS = {
        '160': '#8b4513', '80': '#4682b4', '60': '#20b2aa', '40': '#00ff00',
        '30': '#9acd32', '20': '#ffd700', '17': '#ff8c00', '15': '#f08080',
        '12': '#da70d6', '10': '#9370db', '6': '#00ced1', '2': '#e0e0e0'
    };
    function getBandColor(settings, bandId) {
        if (!bandId) return null;
        var key = 'band_' + bandId + '_color';
        var c = settings && (settings[key] !== undefined && settings[key] !== null && settings[key] !== '') ? String(settings[key]).trim() : null;
        if (c && /^#[0-9A-Fa-f]{3,8}$/.test(c)) return c;
        return DEFAULT_BAND_COLORS[bandId] || '#ccc';
    }
    function freqToBand(khz) {
        if (khz == null || isNaN(khz)) return null;
        var k = parseInt(khz, 10);
        for (var i = 0; i < BANDS.length; i++) {
            if (k >= BANDS[i].minKHz && k <= BANDS[i].maxKHz) return BANDS[i].id;
        }
        return null;
    }
    function isBandEnabled(settings, bandId) {
        if (!settings) return true;
        var key = 'band_' + bandId;
        var v = settings[key];
        if (v === false || v === 'false' || v === '0' || v === 0) return false;
        return true;
    }
    function getCellSettings(cell) {
        var allSettings = window.GLANCERF_MODULE_SETTINGS || {};
        var r = cell.getAttribute('data-row');
        var c = cell.getAttribute('data-col');
        var key = (r != null && c != null) ? r + '_' + c : '';
        return (key && allSettings[key]) ? allSettings[key] : {};
    }
    function setState(cell, state) {
        cell.classList.remove('live_spots_state_loading', 'live_spots_state_error', 'live_spots_state_empty');
        if (state) cell.classList.add('live_spots_state_' + state);
    }
    function showLoading(cell, on) {
        var wrap = cell.querySelector('.live_spots_wrap');
        var loadEl = cell.querySelector('.live_spots_loading');
        var errEl = cell.querySelector('.live_spots_error');
        var emptyEl = cell.querySelector('.live_spots_empty');
        var listWrap = cell.querySelector('.live_spots_list_wrap');
        var tableWrap = cell.querySelector('.live_spots_table_wrap');
        if (!wrap) return;
        if (on) {
            if (errEl) errEl.style.display = 'none';
            if (emptyEl) emptyEl.style.display = 'none';
            if (listWrap) listWrap.style.display = 'none';
            if (tableWrap) tableWrap.style.display = 'none';
            if (loadEl) loadEl.style.display = '';
        } else if (loadEl) loadEl.style.display = 'none';
    }
    function setFilterNote(cell, filterMode, callsignOrGrid, displayMode, ageMins) {
        var el = cell.querySelector('.live_spots_filter_note');
        if (!el) return;
        if (!callsignOrGrid) {
            el.textContent = '';
            el.style.display = 'none';
            return;
        }
        var label = (filterMode === 'sent') ? 'Sent from ' : 'Heard by ';
        var text = label + callsignOrGrid;
        if (displayMode === 'table' && ageMins >= 1) {
            text += ' (last ' + ageMins + ' min)';
        }
        el.textContent = text;
        el.style.display = '';
    }
    function setLastRefresh(cell, show) {
        var el = cell.querySelector('.live_spots_last_refresh');
        if (!el) return;
        if (!show) {
            el.textContent = '';
            el.style.display = 'none';
            return;
        }
        var d = new Date();
        var day = d.getDate();
        var m = d.getMonth() + 1;
        var t = String(d.getHours()).padStart(2, '0') + ':' + String(d.getMinutes()).padStart(2, '0');
        el.textContent = 'Last refreshed: ' + day + ' ' + ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][m - 1] + ' ' + t;
        el.style.display = '';
    }
    function showError(cell, msg) {
        var errEl = cell.querySelector('.live_spots_error');
        var loadEl = cell.querySelector('.live_spots_loading');
        var emptyEl = cell.querySelector('.live_spots_empty');
        var listWrap = cell.querySelector('.live_spots_list_wrap');
        var tableWrap = cell.querySelector('.live_spots_table_wrap');
        if (loadEl) loadEl.style.display = 'none';
        if (emptyEl) emptyEl.style.display = 'none';
        if (listWrap) listWrap.style.display = 'none';
        if (tableWrap) tableWrap.style.display = 'none';
        if (errEl) { errEl.textContent = msg || 'Error'; errEl.style.display = ''; }
        setFilterNote(cell, null, null, null, null);
        setLastRefresh(cell, false);
    }
    function showEmpty(cell, msg) {
        var loadEl = cell.querySelector('.live_spots_loading');
        var emptyEl = cell.querySelector('.live_spots_empty');
        var errEl = cell.querySelector('.live_spots_error');
        var listWrap = cell.querySelector('.live_spots_list_wrap');
        var tableWrap = cell.querySelector('.live_spots_table_wrap');
        if (loadEl) loadEl.style.display = 'none';
        if (errEl) errEl.style.display = 'none';
        if (listWrap) listWrap.style.display = 'none';
        if (tableWrap) tableWrap.style.display = 'none';
        if (emptyEl) { emptyEl.textContent = msg || 'No spots'; emptyEl.style.display = ''; }
        setFilterNote(cell, null, null, null, null);
        setLastRefresh(cell, false);
        setState(cell, 'empty');
    }
    function formatFreqHz(hz) {
        if (hz === undefined || hz === null || hz === '') return '—';
        var n = parseInt(String(hz).trim(), 10);
        if (isNaN(n)) return String(hz);
        if (n >= 1000000) return (n / 1000000).toFixed(3) + ' MHz';
        if (n >= 1000) return (n / 1000).toFixed(1) + ' kHz';
        return n + ' Hz';
    }
    function freqToKHz(hz) {
        var n = parseInt(String(hz).trim(), 10);
        if (isNaN(n)) return null;
        return Math.round(n / 1000);
    }
    function formatTime(secStr) {
        if (!secStr) return '—';
        var s = parseInt(String(secStr), 10);
        if (isNaN(s)) return String(secStr);
        var d = new Date(s * 1000);
        var h = d.getUTCHours();
        var m = d.getUTCMinutes();
        return (h < 10 ? '0' : '') + h + ':' + (m < 10 ? '0' : '') + m + 'Z';
    }
    function escapeHtml(s) {
        if (s == null) return '';
        var t = document.createTextNode(String(s));
        var div = document.createElement('div');
        div.appendChild(t);
        return div.innerHTML;
    }
    function renderList(cell, spots, filterMode, settings) {
        var listWrap = cell.querySelector('.live_spots_list_wrap');
        var listEl = cell.querySelector('.live_spots_list');
        var emptyEl = cell.querySelector('.live_spots_empty');
        var tableWrap = cell.querySelector('.live_spots_table_wrap');
        if (cell.querySelector('.live_spots_loading')) cell.querySelector('.live_spots_loading').style.display = 'none';
        if (cell.querySelector('.live_spots_error')) cell.querySelector('.live_spots_error').style.display = 'none';
        if (emptyEl) emptyEl.style.display = 'none';
        if (tableWrap) tableWrap.style.display = 'none';
        if (!listWrap || !listEl) return;
        listWrap.style.display = '';
        listEl.innerHTML = '';
        if (!spots || spots.length === 0) {
            showEmpty(cell, 'No spots in time range');
            listWrap.style.display = 'none';
            setState(cell, 'empty');
            return;
        }
        setState(cell, '');
        var sorted = spots.slice().sort(function(a, b) {
            var sa = parseInt(a.flowStartSeconds || 0, 10);
            var sb = parseInt(b.flowStartSeconds || 0, 10);
            return sb - sa;
        });
        sorted.forEach(function(s) {
            var call = (filterMode === 'sent') ? (s.receiverCallsign || '—') : (s.senderCallsign || '—');
            var freq = formatFreqHz(s.frequency);
            var mode = (s.mode || '—').toString().trim();
            var time = formatTime(s.flowStartSeconds);
            var khz = freqToKHz(s.frequency);
            var bandId = freqToBand(khz);
            var bandColor = getBandColor(settings, bandId);
            var li = document.createElement('li');
            li.className = 'live_spots_list_item';
            if (bandColor) {
                li.style.borderLeftColor = bandColor;
                li.style.borderLeftWidth = '3px';
                li.style.borderLeftStyle = 'solid';
            }
            li.innerHTML = '<span class="live_spots_list_call">' + escapeHtml(call) + '</span> ' +
                '<span class="live_spots_list_freq">' + escapeHtml(freq) + '</span> ' +
                '<span class="live_spots_list_mode">' + escapeHtml(mode) + '</span> ' +
                '<span class="live_spots_list_time">' + escapeHtml(time) + '</span>';
            if (bandColor) {
                var callSpan = li.querySelector('.live_spots_list_call');
                if (callSpan) callSpan.style.color = bandColor;
            }
            listEl.appendChild(li);
        });
    }
    function renderTable(cell, spots, settings) {
        var tableWrap = cell.querySelector('.live_spots_table_wrap');
        var gridEl = cell.querySelector('.live_spots_bands_grid');
        var listWrap = cell.querySelector('.live_spots_list_wrap');
        var emptyEl = cell.querySelector('.live_spots_empty');
        if (cell.querySelector('.live_spots_loading')) cell.querySelector('.live_spots_loading').style.display = 'none';
        if (cell.querySelector('.live_spots_error')) cell.querySelector('.live_spots_error').style.display = 'none';
        if (emptyEl) emptyEl.style.display = 'none';
        if (listWrap) listWrap.style.display = 'none';
        if (!tableWrap || !gridEl) return;
        tableWrap.style.display = '';
        gridEl.innerHTML = '';
        if (!spots || spots.length === 0) {
            showEmpty(cell, 'No spots in time range');
            tableWrap.style.display = 'none';
            setState(cell, 'empty');
            return;
        }
        var byBand = {};
        BANDS.forEach(function(b) { byBand[b.id] = 0; });
        spots.forEach(function(s) {
            var khz = freqToKHz(s.frequency);
            var bandId = freqToBand(khz);
            if (bandId) byBand[bandId] = (byBand[bandId] || 0) + 1;
        });
        var bandsWithCounts = BANDS.filter(function(b) {
            return isBandEnabled(settings, b.id);
        }).map(function(b) {
            return { id: b.id, name: b.name, count: byBand[b.id] || 0 };
        });
        if (bandsWithCounts.length === 0) {
            showEmpty(cell, 'Enable at least one band in config');
            tableWrap.style.display = 'none';
            setState(cell, 'empty');
            return;
        }
        setState(cell, '');
        bandsWithCounts.forEach(function(b) {
            var card = document.createElement('div');
            card.className = 'live_spots_band_card';
            var color = b.count > 0 ? getBandColor(settings, b.id) : null;
            card.innerHTML = '<span class="live_spots_band_name">' + escapeHtml(b.name) + 'm</span>' +
                '<span class="live_spots_band_count">' + escapeHtml(String(b.count)) + '</span>';
            if (color) {
                card.style.borderColor = color;
                var nameEl = card.querySelector('.live_spots_band_name');
                var countEl = card.querySelector('.live_spots_band_count');
                if (nameEl) nameEl.style.color = color;
                if (countEl) countEl.style.color = color;
            } else {
                card.classList.add('live_spots_band_card_zero');
            }
            gridEl.appendChild(card);
        });
    }
    function updateCell(cell) {
        var settings = getCellSettings(cell);
        var callsignOrGrid = (settings.callsign_or_grid || '').toString().trim();
        if (!callsignOrGrid) {
            showEmpty(cell, 'Set callsign or grid in config');
            setState(cell, 'empty');
            return;
        }
        var filterMode = (settings.filter_mode || 'received').toString().trim().toLowerCase();
        var displayMode = (settings.display_mode || 'list').toString().trim().toLowerCase();
        var ageMins = parseInt(settings.age_mins, 10);
        if (isNaN(ageMins) || ageMins < 1) ageMins = 60;
        setFilterNote(cell, filterMode, callsignOrGrid, displayMode, ageMins);
        showLoading(cell, true);
        setState(cell, 'loading');
        var url = '/api/live_spots/spots?filter_mode=' + encodeURIComponent(filterMode) +
            '&callsign_or_grid=' + encodeURIComponent(callsignOrGrid) +
            '&age_mins=' + ageMins;
        fetch(url)
            .then(function(res) { return res.json(); })
            .then(function(data) {
                showLoading(cell, false);
                if (!data || data.ok !== true) {
                    showError(cell, (data && data.error) ? data.error : 'Request failed');
                    setState(cell, 'error');
                    return;
                }
                var spots = data.spots || [];
                if (displayMode === 'table') {
                    renderTable(cell, spots, settings);
                } else {
                    renderList(cell, spots, filterMode, settings);
                }
                setLastRefresh(cell, true);
            })
            .catch(function(err) {
                showLoading(cell, false);
                showError(cell, err && err.message ? err.message : 'Network error');
                setState(cell, 'error');
            });
    }
    function runAll() {
        document.querySelectorAll('.grid-cell-live_spots').forEach(function(cell) {
            updateCell(cell);
        });
    }
    runAll();
    setInterval(runAll, REFRESH_MS);
})();
