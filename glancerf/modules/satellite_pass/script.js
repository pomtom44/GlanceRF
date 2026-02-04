(function() {
    var UPDATE_MS = 45000;

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
                lon = -180 + c0 * 20 + (parseInt(d0, 10)) * 2 + 1;
                lat = -90 + c1 * 10 + (parseInt(d1, 10)) * 1 + 0.5;
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

    function formatUtcToLocalHhMm(isoStr) {
        if (!isoStr || typeof isoStr !== 'string') return '';
        try {
            var d = new Date(isoStr.replace('Z', ''));
            var h = d.getHours();
            var m = d.getMinutes();
            return (h < 10 ? '0' : '') + h + ':' + (m < 10 ? '0' : '') + m;
        } catch (e) {
            return '';
        }
    }

    function formatMinutesFromNow(isoStr) {
        if (!isoStr || typeof isoStr !== 'string') return null;
        try {
            var d = new Date(isoStr.replace('Z', ''));
            var diff = (d - new Date()) / 60000;
            return Math.round(diff);
        } catch (e) {
            return null;
        }
    }

    function formatDuration(sec) {
        if (sec == null || sec < 0) return '';
        var m = Math.floor(sec / 60);
        var s = sec % 60;
        if (m >= 60) {
            var h = Math.floor(m / 60);
            m = m % 60;
            return h + 'h' + (m < 10 ? '0' : '') + m + 'm';
        }
        return m + 'm' + (s > 0 ? ' ' + s + 's' : '');
    }

    function deg2rad(d) { return d * Math.PI / 180; }

    /* Sky dome drawn like HamClock (ESPHamClock earthsat.cpp drawSatSkyDome):
     * North up, zenith at center, horizon circle, radial spokes every 30 deg,
     * elevation rings at 30/60 deg, pass as smooth polyline, S at set, max el + duration label.
     */
    function drawSkyDome(canvas, passData, currentAz, currentEl) {
        var ctx = canvas.getContext('2d');
        var w = canvas.width;
        var h = canvas.height;
        ctx.clearRect(0, 0, w, h);
        var r0 = Math.min(w, h) * 0.45;
        var cx = w / 2;
        var cy = h / 2;

        var gridColor = '#333333';
        var labelColor = '#888888';
        var accentColor = '#0f0';

        function elToR(el) {
            return r0 * (90 - Math.max(-5, Math.min(95, el))) / 90;
        }
        function azElToXY(az, el) {
            var r = elToR(el);
            var a = deg2rad(az);
            return { x: cx + r * Math.sin(a), y: cy - r * Math.cos(a) };
        }

        ctx.fillStyle = '#000000';
        ctx.fillRect(0, 0, w, h);

        ctx.strokeStyle = gridColor;
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.arc(cx, cy, r0, 0, Math.PI * 2);
        ctx.stroke();

        for (var a = 0; a < 360; a += 30) {
            var p = azElToXY(a, 0);
            ctx.strokeStyle = gridColor;
            ctx.beginPath();
            ctx.moveTo(cx, cy);
            ctx.lineTo(p.x, p.y);
            ctx.stroke();
            ctx.fillStyle = accentColor;
            ctx.beginPath();
            ctx.arc(p.x, p.y, 1, 0, Math.PI * 2);
            ctx.fill();
        }

        [30, 60].forEach(function(el) {
            var r = r0 * (90 - el) / 90;
            ctx.strokeStyle = gridColor;
            ctx.beginPath();
            ctx.arc(cx, cy, r, 0, Math.PI * 2);
            ctx.stroke();
        });

        ctx.fillStyle = labelColor;
        ctx.font = '13px sans-serif';
        ctx.textAlign = 'left';
        ctx.textBaseline = 'top';
        ctx.fillText('NW', cx - r0, cy - r0 + 2);
        ctx.fillText('NE', cx + r0 - 18, cy - r0 + 2);
        ctx.fillText('SW', cx - r0, cy + r0 - 10);
        ctx.fillText('SE', cx + r0 - 18, cy + r0 - 10);

        if (passData && passData.next_pass) {
            var np = passData.next_pass;
            var riseAz = np.rise_az != null ? np.rise_az : 0;
            var setAz = np.set_az != null ? np.set_az : 180;
            var maxEl = np.max_el != null ? np.max_el : 45;
            var durationSec = np.duration_sec != null ? np.duration_sec : 0;
            var deltaAz = setAz - riseAz;
            if (deltaAz > 180) deltaAz -= 360;
            if (deltaAz < -180) deltaAz += 360;
            var nSteps = 24;
            var prev = null;
            var maxElPt = null;
            var maxElVal = 0;
            for (var i = 0; i <= nSteps; i++) {
                var t = i / nSteps;
                var el = 4 * maxEl * t * (1 - t);
                var az = riseAz + t * deltaAz;
                var pt = azElToXY(az, el);
                if (el > maxElVal) {
                    maxElVal = el;
                    maxElPt = { x: pt.x, y: pt.y };
                }
                if (prev !== null) {
                    ctx.strokeStyle = accentColor;
                    ctx.lineWidth = 1.5;
                    ctx.beginPath();
                    ctx.moveTo(prev.x, prev.y);
                    ctx.lineTo(pt.x, pt.y);
                    ctx.stroke();
                }
                prev = pt;
            }
            var setPt = azElToXY(setAz, 0);
            var sx = setPt.x + (setPt.x > cx ? -12 : 2);
            var sy = setPt.y + (setPt.y > cy ? 4 : -8);
            ctx.fillStyle = accentColor;
            ctx.font = '13px sans-serif';
            ctx.textAlign = 'left';
            ctx.textBaseline = 'top';
            ctx.fillText('S', sx, sy);
            if (maxElPt && maxElVal > 0 && r0 > 40) {
                var mx = maxElPt.x + (maxElPt.x > cx ? -28 : 12);
                var my = maxElPt.y + (maxElPt.y < cy ? -16 : 6);
                ctx.fillStyle = labelColor;
                ctx.fillText(Math.round(maxEl) + '\u00B0', mx, my);
                if (durationSec > 0) {
                    var mins = Math.floor(durationSec / 60);
                    var secs = durationSec % 60;
                    var durStr = mins >= 60 ? (Math.floor(mins / 60) + 'h' + (mins % 60 < 10 ? '0' : '') + (mins % 60)) : (mins + ':' + (secs < 10 ? '0' : '') + secs);
                    ctx.fillText(durStr, mx, my + 11);
                }
            }
        }

        if (currentAz != null && currentEl != null && currentEl >= -5) {
            var pos = azElToXY(currentAz, currentEl);
            ctx.fillStyle = accentColor;
            ctx.beginPath();
            ctx.arc(pos.x, pos.y, 2, 0, Math.PI * 2);
            ctx.fill();
        }
    }

    function setState(cell, state) {
        cell.classList.remove('satellite_pass_state_empty', 'satellite_pass_state_loading', 'satellite_pass_state_error');
        if (state) cell.classList.add('satellite_pass_state_' + state);
    }

    function updateCell(cell) {
        var allSettings = window.GLANCERF_MODULE_SETTINGS || {};
        var r = cell.getAttribute('data-row');
        var c = cell.getAttribute('data-col');
        var cellKey = (r != null && c != null) ? r + '_' + c : '';
        var ms = (cellKey && allSettings[cellKey]) ? allSettings[cellKey] : {};
        var locStr = (ms.location || window.GLANCERF_SETUP_LOCATION || '').toString().trim();
        var selectedStr = (ms.selected_satellites || '[]').toString().trim();
        var selected = [];
        try {
            if (selectedStr) selected = JSON.parse(selectedStr);
            if (!Array.isArray(selected)) selected = [];
        } catch (e) { selected = []; }

        var nameEl = cell.querySelector('.satellite_pass_name');
        var eventsEl = cell.querySelector('.satellite_pass_events');
        var infoEl = cell.querySelector('.satellite_pass_info');
        var azelEl = cell.querySelector('.satellite_pass_azel');
        var canvas = cell.querySelector('.satellite_pass_canvas');
        var wrap = cell.querySelector('.satellite_pass_wrap');

        if (!selected.length) {
            setState(cell, 'empty');
            if (nameEl) nameEl.textContent = '';
            if (eventsEl) eventsEl.textContent = '';
            if (infoEl) infoEl.textContent = '';
            if (azelEl) azelEl.textContent = '';
            return;
        }

        var loc = parseLocation(locStr);
        if (!loc) {
            setState(cell, 'empty');
            if (nameEl) nameEl.textContent = '';
            if (eventsEl) eventsEl.textContent = 'Set location (grid or lat,lng)';
            if (infoEl) infoEl.textContent = '';
            if (azelEl) azelEl.textContent = '';
            return;
        }

        setState(cell, 'loading');
        var noradIds = selected.slice(0, 20).join(',');
        var url = '/api/satellite/passes?norad_ids=' + encodeURIComponent(noradIds) + '&lat=' + loc.lat + '&lng=' + loc.lng + '&alt=0';
        fetch(url).then(function(r) { return r.json(); }).then(function(data) {
            setState(cell, '');
            var passes = (data && data.passes) ? data.passes : [];
            if (passes.length === 0) {
                if (nameEl) nameEl.textContent = '';
                if (eventsEl) eventsEl.textContent = 'No pass data';
                if (infoEl) infoEl.textContent = '';
                if (azelEl) azelEl.textContent = '';
                if (canvas) drawSkyDome(canvas, null, null, null);
                return;
            }
            var sat = passes[0];
            if (nameEl) nameEl.textContent = sat.name || ('NORAD ' + sat.norad_id);
            var cur = sat.current || {};
            var np = sat.next_pass;
            var riseUtc = np && np.rise_utc;
            var setUtc = np && np.set_utc;
            var riseMin = riseUtc ? formatMinutesFromNow(riseUtc) : null;
            var setMin = setUtc ? formatMinutesFromNow(setUtc) : null;
            var riseTime = riseUtc ? formatUtcToLocalHhMm(riseUtc) : '';
            var setTime = setUtc ? formatUtcToLocalHhMm(setUtc) : '';
            var riseAzStr = np && np.rise_az != null ? ' @ ' + Math.round(np.rise_az) + '\u00B0' : '';
            var setAzStr = np && np.set_az != null ? ' @ ' + Math.round(np.set_az) + '\u00B0' : '';
            if (eventsEl) {
                if (cur.up && setUtc != null) {
                    eventsEl.innerHTML = 'Set in ' + (setMin != null ? setMin + 'm' : setTime) + setAzStr;
                } else if (riseUtc != null && setUtc != null) {
                    eventsEl.innerHTML = 'Rise in ' + (riseMin != null ? riseMin + 'm' : riseTime) + riseAzStr + '<br>Set ' + (setMin != null ? setMin + 'm' : setTime) + setAzStr;
                } else if (riseUtc != null) {
                    eventsEl.innerHTML = 'Rise in ' + (riseMin != null ? riseMin + 'm' : riseTime) + riseAzStr;
                } else {
                    eventsEl.textContent = np ? 'No pass in next 2 days' : '';
                }
            }
            if (infoEl) {
                if (np && riseUtc && setUtc) {
                    var durStr = formatDuration(np.duration_sec);
                    var maxElStr = np.max_el != null ? Math.round(np.max_el) + '\u00B0' : '';
                    var parts = [];
                    parts.push('Rise ' + riseTime + (np.rise_az != null ? ' (' + Math.round(np.rise_az) + '\u00B0)' : ''));
                    parts.push('Set ' + setTime + (np.set_az != null ? ' (' + Math.round(np.set_az) + '\u00B0)' : ''));
                    if (durStr) parts.push(durStr + ' in view');
                    if (maxElStr) parts.push('max ' + maxElStr);
                    infoEl.textContent = parts.join('  |  ');
                } else {
                    infoEl.textContent = '';
                }
            }
            if (azelEl) {
                var azelParts = [];
                azelParts.push('Az ' + (cur.az != null ? Math.round(cur.az) : '-'));
                azelParts.push('El ' + (cur.el != null ? Math.round(cur.el) : '-'));
                if (cur.up) azelParts.push('Up');
                else azelParts.push('Below horizon');
                azelEl.textContent = azelParts.join('  ');
            }
            if (canvas) {
                var container = cell.querySelector('.satellite_pass_dome_wrap');
                var rect = container ? container.getBoundingClientRect() : { width: 200, height: 160 };
                var cw = Math.max(1, Math.floor(rect.width || 200));
                var ch = Math.max(1, Math.floor(rect.height || 160));
                if (canvas.width !== cw || canvas.height !== ch) {
                    canvas.width = cw;
                    canvas.height = ch;
                }
                drawSkyDome(canvas, sat, cur.az, cur.el);
            }
        }).catch(function() {
            setState(cell, 'error');
            var errEl = cell.querySelector('.satellite_pass_error');
            if (errEl) errEl.textContent = 'Failed to load pass data.';
            if (nameEl) nameEl.textContent = '';
            if (eventsEl) eventsEl.textContent = '';
            if (infoEl) infoEl.textContent = '';
            if (azelEl) azelEl.textContent = '';
        });
    }

    function run() {
        document.querySelectorAll('.grid-cell-satellite_pass').forEach(function(cell) {
            updateCell(cell);
        });
    }

    run();
    setInterval(run, UPDATE_MS);
})();
