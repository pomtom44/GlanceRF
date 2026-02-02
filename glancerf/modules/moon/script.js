(function() {
            var CACHE_MS = 60 * 60 * 1000;
            function isOn(val) {
                return val === '1' || val === 1 || val === true || val === 'true';
            }
            function maidenheadToLatLng(s) {
                var str = (s || '').toString().trim().toUpperCase();
                if (str.length < 2) return null;
                var c0 = str.charCodeAt(0) - 65;
                var c1 = str.charCodeAt(1) - 65;
                if (c0 < 0 || c0 > 17 || c1 < 0 || c1 > 17) return null;
                var lon = -180 + c0 * 20 + 10;
                var lat = -90 + c1 * 10 + 5;
                if (str.length >= 4) {
                    var d0 = str.charAt(2), d1 = str.charAt(3);
                    if (d0 >= '0' && d0 <= '9' && d1 >= '0' && d1 <= '9') {
                        lon = -180 + c0 * 20 + (d0 - '0') * 2 + 1;
                        lat = -90 + c1 * 10 + (d1 - '0') * 1 + 0.5;
                    }
                }
                if (str.length >= 6) {
                    var sx = str.charAt(4).toLowerCase(), sy = str.charAt(5).toLowerCase();
                    var s0 = sx.charCodeAt(0) - 97, s1 = sy.charCodeAt(0) - 97;
                    if (s0 >= 0 && s0 <= 23 && s1 >= 0 && s1 <= 23) {
                        lon = -180 + c0 * 20 + (str.charAt(2) - '0') * 2 + (s0 + 0.5) * (2/24);
                        lat = -90 + c1 * 10 + (str.charAt(3) - '0') * 1 + (s1 + 0.5) * (1/24);
                    }
                }
                return { lat: lat, lng: lon };
            }
            function parseLocation(s) {
                s = (s || '').toString().trim();
                if (!s) return null;
                var m = s.match(/^\s*(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)\s*$/);
                if (m) {
                    var la = parseFloat(m[1]), lo = parseFloat(m[2]);
                    if (!isNaN(la) && !isNaN(lo) && la >= -90 && la <= 90 && lo >= -180 && lo <= 180)
                        return { lat: la, lng: lo };
                }
                return maidenheadToLatLng(s);
            }
            function formatTimeFromIso(isoStr) {
                if (!isoStr || typeof isoStr !== 'string') return '';
                var idx = isoStr.indexOf('T');
                if (idx === -1) return '';
                var timePart = isoStr.slice(idx + 1);
                var match = timePart.match(/^(\d{1,2}):(\d{2})/);
                return match ? match[1].padStart(2, '0') + ':' + match[2] : '';
            }
            var LUNAR_CYCLE_DAYS = 29.530588;
            var KNOWN_NEW_MOON_JD = 2451550.1;
            function moonPhaseName(ageDays) {
                if (ageDays < 1.845) return 'New Moon';
                if (ageDays < 7.38) return 'Waxing Crescent';
                if (ageDays < 9.225) return 'First Quarter';
                if (ageDays < 14.765) return 'Waxing Gibbous';
                if (ageDays < 16.61) return 'Full Moon';
                if (ageDays < 22.15) return 'Waning Gibbous';
                if (ageDays < 23.995) return 'Last Quarter';
                if (ageDays < 29.53) return 'Waning Crescent';
                return 'New Moon';
            }
            function getMoonPhaseForDate(date) {
                var jd = (date.getTime() / 86400000) + 2440587.5;
                var age = (jd - KNOWN_NEW_MOON_JD) % LUNAR_CYCLE_DAYS;
                if (age < 0) age += LUNAR_CYCLE_DAYS;
                return { ageDays: age, name: moonPhaseName(age) };
            }
            function showElements(cell, data, ms) {
                var phaseLabelEl = cell.querySelector('.moon_phase_label');
                var phaseIconEl = cell.querySelector('.moon_phase_icon');
                var moonriseEl = cell.querySelector('.moon_moonrise');
                var moonsetEl = cell.querySelector('.moon_moonset');
                var errEl = cell.querySelector('.moon_error');
                var loadEl = cell.querySelector('.moon_loading');
                if (errEl) { errEl.style.display = 'none'; errEl.textContent = ''; }
                if (loadEl) loadEl.style.display = 'none';
                if (isOn(ms.show_phase)) {
                    var phase = getMoonPhaseForDate(new Date());
                    if (phaseLabelEl) {
                        phaseLabelEl.textContent = phase.name;
                        phaseLabelEl.style.display = '';
                    }
                    if (phaseIconEl) phaseIconEl.style.display = 'none';
                } else {
                    if (phaseLabelEl) phaseLabelEl.style.display = 'none';
                    if (phaseIconEl) phaseIconEl.style.display = 'none';
                }
                if (data && data.daily) {
                    var mrStr = data.daily.moonrise && data.daily.moonrise[0] ? formatTimeFromIso(data.daily.moonrise[0]) : '';
                    var msStr = data.daily.moonset && data.daily.moonset[0] ? formatTimeFromIso(data.daily.moonset[0]) : '';
                    if (moonriseEl && isOn(ms.show_moonrise)) {
                        moonriseEl.textContent = mrStr ? ('Moonrise ' + mrStr) : '';
                        moonriseEl.style.display = mrStr ? '' : 'none';
                    } else if (moonriseEl) moonriseEl.style.display = 'none';
                    if (moonsetEl && isOn(ms.show_moonset)) {
                        moonsetEl.textContent = msStr ? ('Moonset ' + msStr) : '';
                        moonsetEl.style.display = msStr ? '' : 'none';
                    } else if (moonsetEl) moonsetEl.style.display = 'none';
                } else {
                    if (moonriseEl) moonriseEl.style.display = 'none';
                    if (moonsetEl) moonsetEl.style.display = 'none';
                }
            }
            function showError(cell, msg) {
                var errEl = cell.querySelector('.moon_error');
                var loadEl = cell.querySelector('.moon_loading');
                if (loadEl) loadEl.style.display = 'none';
                if (errEl) { errEl.textContent = msg || 'Error'; errEl.style.display = ''; }
            }
            function showLoading(cell, on) {
                var loadEl = cell.querySelector('.moon_loading');
                var errEl = cell.querySelector('.moon_error');
                if (on) {
                    if (errEl) errEl.style.display = 'none';
                    if (loadEl) { loadEl.textContent = 'Loading...'; loadEl.style.display = ''; }
                } else if (loadEl) loadEl.style.display = 'none';
            }
            function fetchMoonTimes(cell, cellKey, ms, coord, cb) {
                showLoading(cell, true);
                var url = 'https://api.open-meteo.com/v1/forecast?latitude=' + encodeURIComponent(coord.lat) + '&longitude=' + encodeURIComponent(coord.lng) +
                    '&daily=moonrise,moonset&timezone=auto';
                fetch(url).then(function(r) {
                    return r.json().then(function(data) {
                        return { ok: r.ok, status: r.status, data: data };
                    });
                }).then(function(result) {
                    showLoading(cell, false);
                    var data = result.data;
                    if (result.ok && data) {
                        cb(data);
                        try {
                            window['moon_cache_' + cellKey] = { data: data, ts: Date.now() };
                        } catch (e) {}
                    } else {
                        var msg = 'Moon times unavailable';
                        if (data && typeof data.reason === 'string') msg = data.reason;
                        else if (data && typeof data.error === 'string') msg = data.error;
                        else if (!result.ok && result.status) msg = 'Moon times unavailable (' + result.status + ')';
                        cb(null, msg);
                    }
                }).catch(function(err) {
                    showLoading(cell, false);
                    var msg = (err && err.message) ? err.message : 'Network error';
                    cb(null, msg);
                });
            }
            function updateCell(cell, cellKey, ms) {
                var locStr = (ms.location || window.GLANCERF_SETUP_LOCATION || '').toString().trim();
                var coord = parseLocation(locStr);
                if (!coord) {
                    showError(cell, 'Set grid or lat,lng');
                    return;
                }
                var cacheKey = 'moon_cache_' + cellKey;
                try {
                    var cached = window[cacheKey];
                    if (cached && (Date.now() - cached.ts) < CACHE_MS) {
                        showLoading(cell, false);
                        showElements(cell, cached.data, ms);
                        return;
                    }
                } catch (e) {}
                fetchMoonTimes(cell, cellKey, ms, coord, function(data, errorMsg) {
                    if (data) {
                        showElements(cell, data, ms);
                    } else {
                        showElements(cell, null, ms);
                        showError(cell, errorMsg || 'Moon times unavailable');
                    }
                });
            }
            function runAll() {
                var allSettings = window.GLANCERF_MODULE_SETTINGS || {};
                document.querySelectorAll('.grid-cell-moon').forEach(function(cell) {
                    var r = cell.getAttribute('data-row');
                    var c = cell.getAttribute('data-col');
                    var cellKey = (r != null && c != null) ? r + '_' + c : '';
                    var ms = (cellKey && allSettings[cellKey]) ? allSettings[cellKey] : {};
                    updateCell(cell, cellKey, ms);
                });
            }
            runAll();
            setInterval(runAll, 60 * 60 * 1000);
        })();
