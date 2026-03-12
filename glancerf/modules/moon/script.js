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
    function dateToTimeIso(d) {
        if (!d) return '';
        var getH = d.getHours, getM = d.getMinutes;
        if (typeof getH !== 'function' || typeof getM !== 'function') return '';
        var y = d.getFullYear(), m = d.getMonth() + 1, day = d.getDate();
        var h = getH.call(d), min = getM.call(d);
        return y + '-' + String(m).padStart(2, '0') + '-' + String(day).padStart(2, '0') + 'T' +
            String(h).padStart(2, '0') + ':' + String(min).padStart(2, '0') + ':00';
    }
    function sunCalcReady() {
        var sc = window.SunCalc;
        return sc && (typeof sc.getMoonTimes === 'function' || typeof sc.getTimes === 'function' || typeof sc === 'function');
    }
    function loadSunCalc(cb) {
        if (sunCalcReady()) { cb(); return; }
        var id = 'script-suncalc-glancerf';
        if (document.getElementById(id)) {
            var t = setInterval(function() {
                if (sunCalcReady()) { clearInterval(t); cb(); }
            }, 50);
            return;
        }
        var s = document.createElement('script');
        s.id = id;
        s.src = 'https://cdnjs.cloudflare.com/ajax/libs/suncalc/1.9.0/suncalc.min.js';
        s.onload = function() { cb(); };
        s.onerror = function() { cb(); };
        document.head.appendChild(s);
    }
    var LUNAR_CYCLE_DAYS = 29.530588;
    var KNOWN_NEW_MOON_JD = 2451550.1;
    var _moonGradId = 0;
    var MOON_PHASE_PNG = [
        'https://img.icons8.com/?size=96&id=Wdnu-edbShJS&format=png',
        'https://img.icons8.com/?size=96&id=PGEsjsRXYhtT&format=png',
        'https://img.icons8.com/?size=96&id=cy8DHBgUJqqL&format=png',
        'https://img.icons8.com/?size=96&id=SnlxFjy7u-4t&format=png',
        'https://img.icons8.com/?size=96&id=NJx6Gbc4Ng7C&format=png',
        'https://img.icons8.com/?size=96&id=RLniTqU8gD1y&format=png',
        'https://img.icons8.com/?size=96&id=KIPHVfQWWl4R&format=png',
        'https://img.icons8.com/?size=96&id=JGGPnA5MB09j&format=png'
    ];
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
    function moonPhaseIndex(ageDays) {
        if (ageDays < 1.845) return 0;
        if (ageDays < 7.38) return 1;
        if (ageDays < 9.225) return 2;
        if (ageDays < 14.765) return 3;
        if (ageDays < 16.61) return 4;
        if (ageDays < 22.15) return 5;
        if (ageDays < 23.995) return 6;
        if (ageDays < 29.53) return 7;
        return 0;
    }
    function getMoonPhaseForDate(date) {
        var jd = (date.getTime() / 86400000) + 2440587.5;
        var age = (jd - KNOWN_NEW_MOON_JD) % LUNAR_CYCLE_DAYS;
        if (age < 0) age += LUNAR_CYCLE_DAYS;
        return { ageDays: age, name: moonPhaseName(age), phaseIndex: moonPhaseIndex(age) };
    }
    function moonPhaseSvg(ageDays) {
        var r = 22;
        var illum = 0.5 * (1 - Math.cos(2 * Math.PI * ageDays / LUNAR_CYCLE_DAYS));
        var offset = (2 * illum - 1) * (r + 1);
        var cx = 24;
        var cy = 24;
        var gradId = 'moon-lit-' + (++_moonGradId);
        return '<svg class="moon_phase_svg" viewBox="0 0 48 48" width="48" height="48" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">' +
            '<defs><linearGradient id="' + gradId + '" x1="0%" y1="0%" x2="100%" y2="100%">' +
            '<stop offset="0%" stop-color="#f5ecd8"/><stop offset="100%" stop-color="#d4c8a8"/>' +
            '</linearGradient></defs>' +
            '<circle cx="' + cx + '" cy="' + cy + '" r="' + r + '" fill="url(#' + gradId + ')" stroke="#8a7a5a" stroke-width="0.8"/>' +
            '<circle cx="' + (cx + offset) + '" cy="' + cy + '" r="' + (r + 0.5) + '" fill="var(--moon-shadow, #1a1a1a)"/>' +
            '</svg>';
    }
    function moonPhaseImg(phaseIndex) {
        var url = MOON_PHASE_PNG[phaseIndex] || MOON_PHASE_PNG[0];
        return '<img class="moon_phase_img" src="' + url + '" alt="" width="48" height="48" loading="lazy"/>';
    }
    function showElements(cell, data, ms) {
        var phaseVisualEl = cell.querySelector('.moon_phase_visual');
        var phaseLabelEl = cell.querySelector('.moon_phase_label');
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
            if (phaseVisualEl) {
                phaseVisualEl.innerHTML = moonPhaseImg(phase.phaseIndex);
                phaseVisualEl.style.display = '';
                var img = phaseVisualEl.querySelector('.moon_phase_img');
                if (img) {
                    img.onerror = function() {
                        phaseVisualEl.innerHTML = moonPhaseSvg(phase.ageDays);
                    };
                }
            }
        } else {
            if (phaseLabelEl) phaseLabelEl.style.display = 'none';
            if (phaseVisualEl) phaseVisualEl.style.display = 'none';
        }
        if (data && data.daily) {
            var mrStr = data.daily.moonrise && data.daily.moonrise[0] ? formatTimeFromIso(data.daily.moonrise[0]) : (data.daily.moonriseLabel || '');
            var msStr = data.daily.moonset && data.daily.moonset[0] ? formatTimeFromIso(data.daily.moonset[0]) : (data.daily.moonsetLabel || '');
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
    function getMoonTimesData(coord, cb) {
        loadSunCalc(function() {
            var data = { daily: {} };
            var sc = window.SunCalc;
            if (!sc || typeof sc.getMoonTimes !== 'function') { cb(data); return; }
            try {
                var today = new Date();
                var mt = sc.getMoonTimes(today, coord.lat, coord.lng);
                if (mt.rise) data.daily.moonrise = [dateToTimeIso(mt.rise)];
                if (mt.set) data.daily.moonset = [dateToTimeIso(mt.set)];
                if (mt.alwaysUp) { data.daily.moonriseLabel = 'Always up'; data.daily.moonsetLabel = 'Always up'; }
                if (mt.alwaysDown) { data.daily.moonriseLabel = 'Always down'; data.daily.moonsetLabel = 'Always down'; }
            } catch (e) {}
            cb(data);
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
        var todayKey = new Date().toDateString();
        try {
            var cached = window[cacheKey];
            if (cached && cached.dateKey === todayKey && (Date.now() - cached.ts) < CACHE_MS) {
                showLoading(cell, false);
                showElements(cell, cached.data, ms);
                return;
            }
        } catch (e) {}
        showLoading(cell, true);
        getMoonTimesData(coord, function(data) {
            showLoading(cell, false);
            try {
                window[cacheKey] = { data: data, ts: Date.now(), dateKey: todayKey };
            } catch (e) {}
            showElements(cell, data, ms);
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
