(function() {
            var VALID_MAP_STYLES = ['carto', 'opentopomap', 'esri', 'nasagibs'];
            function maidenheadToLatLng(s) {
                var str = (s || '').toString().trim().toUpperCase();
                if (str.length < 2) return null;
                var c0 = str.charCodeAt(0) - 65;
                var c1 = str.charCodeAt(1) - 65;
                if (c0 < 0 || c0 > 17 || c1 < 0 || c1 > 17) return null;
                var lon = -180 + c0 * 20 + 10;
                var lat = -90 + c1 * 10 + 5;
                if (str.length >= 4) {
                    var d0 = str.charAt(2);
                    var d1 = str.charAt(3);
                    if (d0 >= '0' && d0 <= '9' && d1 >= '0' && d1 <= '9') {
                        lon = -180 + c0 * 20 + (d0 - '0') * 2 + 1;
                        lat = -90 + c1 * 10 + (d1 - '0') * 1 + 0.5;
                    }
                }
                if (str.length >= 6) {
                    var sx = str.charAt(4).toLowerCase();
                    var sy = str.charAt(5).toLowerCase();
                    var s0 = sx.charCodeAt(0) - 97;
                    var s1 = sy.charCodeAt(0) - 97;
                    if (s0 >= 0 && s0 <= 23 && s1 >= 0 && s1 <= 23) {
                        lon = -180 + c0 * 20 + (str.charAt(2) - '0') * 2 + (s0 + 0.5) * (2 / 24);
                        lat = -90 + c1 * 10 + (str.charAt(3) - '0') * 1 + (s1 + 0.5) * (1 / 24);
                    }
                }
                return { lat: lat, lng: lon };
            }
            function parseCenter(centerStr, fallbackLat, fallbackLng) {
                var s = (centerStr || '').toString().trim();
                if (!s) return { lat: fallbackLat, lng: fallbackLng };
                var latLngMatch = s.match(/^\\s*(-?\\d+\\.?\\d*)\\s*,\\s*(-?\\d+\\.?\\d*)\\s*$/);
                if (latLngMatch) {
                    var la = parseFloat(latLngMatch[1]);
                    var lo = parseFloat(latLngMatch[2]);
                    if (!isNaN(la) && !isNaN(lo) && la >= -90 && la <= 90 && lo >= -180 && lo <= 180)
                        return { lat: la, lng: lo };
                }
                var mh = maidenheadToLatLng(s);
                if (mh) return mh;
                return { lat: fallbackLat, lng: fallbackLng };
            }
            function getMapSettings(containerEl) {
                var cell = containerEl.closest('.grid-cell-map');
                if (!cell) return { zoom: 2, lat: 20, lng: 0, map_style: 'carto', tile_style: 'carto_voyager' };
                var allSettings = window.GLANCERF_MODULE_SETTINGS || {};
                var r = cell.getAttribute('data-row');
                var c = cell.getAttribute('data-col');
                var key = (r != null && c != null) ? r + '_' + c : '';
                var ms = (key && allSettings[key]) ? allSettings[key] : {};
                var mapStyle = (ms.map_style && VALID_MAP_STYLES.indexOf(ms.map_style) >= 0) ? ms.map_style : 'carto';
                var tileStyle = ms.tile_style || 'carto_voyager';
                var zoom = 2;
                if (ms.zoom !== undefined && ms.zoom !== '') {
                    var z = parseInt(ms.zoom, 10);
                    if (!isNaN(z) && z >= 0 && z <= 18) zoom = z;
                }
                var fallbackLat = 20, fallbackLng = 0;
                if (ms.center_lat !== undefined && ms.center_lat !== '' && ms.center_lng !== undefined && ms.center_lng !== '') {
                    var fla = parseFloat(ms.center_lat);
                    var flo = parseFloat(ms.center_lng);
                    if (!isNaN(fla) && !isNaN(flo) && fla >= -90 && fla <= 90 && flo >= -180 && flo <= 180) {
                        fallbackLat = fla;
                        fallbackLng = flo;
                    }
                }
                var centerResult = parseCenter(ms.center, fallbackLat, fallbackLng);
                var lat = centerResult.lat, lng = centerResult.lng;
                var gridStyle = (ms.grid_style && ['none', 'tropics', 'latlong', 'maidenhead'].indexOf(ms.grid_style) >= 0) ? ms.grid_style : 'none';
                var showTerminator = (ms.show_terminator === '1' || ms.show_terminator === true);
                var showSunMoon = (ms.show_sun_moon === '1' || ms.show_sun_moon === true);
                var showAurora = (ms.show_aurora === '1' || ms.show_aurora === true);
                var auroraOpacity = 50;
                if (ms.aurora_opacity !== undefined && ms.aurora_opacity !== '') {
                    var ao = parseFloat(ms.aurora_opacity, 10);
                    if (!isNaN(ao) && ao >= 0 && ao <= 100) auroraOpacity = ao;
                }
                return { zoom: zoom, lat: lat, lng: lng, map_style: mapStyle, tile_style: tileStyle, grid_style: gridStyle, show_terminator: showTerminator, show_sun_moon: showSunMoon, show_aurora: showAurora, aurora_opacity: auroraOpacity };
            }
            function getTileLayer(url, options) {
                return L.tileLayer(url, options || {});
            }
            function getTileConfig(mapStyle, tileStyle) {
                if (mapStyle === 'opentopomap') {
                    return getTileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', { subdomains: 'abc', maxZoom: 17 });
                }
                if (mapStyle === 'esri') {
                    return getTileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', { maxZoom: 19 });
                }
                if (mapStyle === 'nasagibs') {
                    return getTileLayer('https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/VIIRS_CityLights_2012/default/default/GoogleMapsCompatible_Level8/{z}/{y}/{x}.jpg', { maxZoom: 8, minZoom: 1 });
                }
                var cartoVariant = 'rastertiles/voyager';
                if (tileStyle === 'carto_positron') cartoVariant = 'light_all';
                else if (tileStyle === 'carto_positron_nolabels') cartoVariant = 'light_nolabels';
                else if (tileStyle === 'carto_dark') cartoVariant = 'dark_all';
                else if (tileStyle === 'carto_dark_nolabels') cartoVariant = 'dark_nolabels';
                return getTileLayer('https://{s}.basemaps.cartocdn.com/' + cartoVariant + '/{z}/{x}/{y}{r}.png', { subdomains: 'abcd', maxZoom: 20 });
            }
            var OVERLAY_STYLE = { color: 'rgba(120,120,140,0.7)', weight: 1 };
            function addGridOverlay(map, gridStyle) {
                if (!gridStyle || gridStyle === 'none' || typeof L === 'undefined') return;
                if (gridStyle === 'tropics') {
                    L.polyline([[-23.44, -180], [-23.44, 180]], OVERLAY_STYLE).addTo(map);
                    L.polyline([[23.44, -180], [23.44, 180]], OVERLAY_STYLE).addTo(map);
                    return;
                }
                if (gridStyle === 'latlong') {
                    var step = 30;
                    for (var lat = -90; lat <= 90; lat += step) {
                        if (lat === -90 || lat === 90) continue;
                        L.polyline([[lat, -180], [lat, 180]], OVERLAY_STYLE).addTo(map);
                    }
                    for (var lon = -180; lon < 180; lon += step) {
                        L.polyline([[-90, lon], [90, lon]], OVERLAY_STYLE).addTo(map);
                    }
                    return;
                }
                if (gridStyle === 'maidenhead') {
                    for (var c0 = 0; c0 < 18; c0++) {
                        var lon = -180 + c0 * 20;
                        L.polyline([[-90, lon], [90, lon]], OVERLAY_STYLE).addTo(map);
                    }
                    for (var c1 = 0; c1 < 18; c1++) {
                        var lat = -90 + c1 * 10;
                        L.polyline([[lat, -180], [lat, 180]], OVERLAY_STYLE).addTo(map);
                    }
                }
            }
            function subsolarLonLat(now) {
                var d = new Date(now);
                var utcHours = d.getUTCHours() + d.getUTCMinutes() / 60 + d.getUTCSeconds() / 3600;
                var dayOfYear = (Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate()) - Date.UTC(d.getUTCFullYear(), 0, 0)) / (24 * 3600 * 1000);
                var decDeg = 23.44 * Math.sin((2 * Math.PI / 365) * (dayOfYear - 81));
                var dRad = (dayOfYear - 1) * 2 * Math.PI / 365;
                var eqTimeMin = -7.655 * Math.sin(dRad) + 9.873 * Math.sin(2 * dRad + 3.588);
                var lon = 15 * (12 - utcHours) - eqTimeMin / 4;
                while (lon > 180) lon -= 360;
                while (lon < -180) lon += 360;
                return { lat: decDeg, lng: lon };
            }
            function sublunarLonLat(now) {
                var d = new Date(now);
                var jd = (d.getTime() / 86400000) + 2440587.5;
                var n = jd - 2451545.0;
                var moonLon = (218.316 + 13.176396 * n) % 360;
                var moonLat = 5.16 * Math.sin((2 * Math.PI / 27.32) * n * 57.3);
                var moonDist = 60.27 - 3.34 * Math.cos((2 * Math.PI / 27.32) * n * 57.3);
                var ra = moonLon - 1.274 * Math.sin((2 * Math.PI / 29.53) * (n - 2));
                var dec = 5.14 * Math.sin((2 * Math.PI / 27.32) * n * 57.3);
                var gmst = (280.46 + 360.9856474 * (jd - 2451545.0)) % 360;
                var lon = (ra - gmst) % 360;
                if (lon > 180) lon -= 360;
                if (lon < -180) lon += 360;
                return { lat: dec, lng: lon };
            }
            function addTerminatorOverlay(map) {
                var now = Date.now();
                var sub = subsolarLonLat(now);
                var decRad = sub.lat * Math.PI / 180;
                var sunLonRad = sub.lng * Math.PI / 180;
                var w = 720;
                var h = 362;
                var canvas = document.createElement('canvas');
                canvas.width = w;
                canvas.height = h;
                var ctx = canvas.getContext('2d');
                var idata = ctx.createImageData(w, h);
                var d = idata.data;
                var twilightDeg = 8;
                for (var y = 0; y < h; y++) {
                    var lat = 90 - ((y + 0.5) / h) * 180;
                    var latRad = lat * Math.PI / 180;
                    var sinLat = Math.sin(latRad);
                    var cosLat = Math.cos(latRad);
                    var sinDec = Math.sin(decRad);
                    var cosDec = Math.cos(decRad);
                    for (var x = 0; x < w; x++) {
                        var lon = -180 + ((x + 0.5) / w) * 360;
                        var lonDiffRad = (lon - sub.lng) * Math.PI / 180;
                        var cosAngle = sinLat * sinDec + cosLat * cosDec * Math.cos(lonDiffRad);
                        var angleRad = Math.acos(Math.max(-1, Math.min(1, cosAngle)));
                        var angleDeg = angleRad * 180 / Math.PI;
                        var nightAlpha = 0;
                        if (angleDeg >= 90 + twilightDeg) {
                            nightAlpha = 0.52;
                        } else if (angleDeg > 90 - twilightDeg) {
                            nightAlpha = 0.52 * (angleDeg - (90 - twilightDeg)) / (2 * twilightDeg);
                        }
                        var i4 = (y * w + x) * 4;
                        d[i4] = 12;
                        d[i4 + 1] = 14;
                        d[i4 + 2] = 26;
                        d[i4 + 3] = Math.round(nightAlpha * 255);
                    }
                }
                ctx.putImageData(idata, 0, 0);
                var url = canvas.toDataURL('image/png');
                L.imageOverlay(url, [[-90, -180], [90, 180]], { opacity: 1 }).addTo(map);
                L.imageOverlay(url, [[-90, 180], [90, 540]], { opacity: 1 }).addTo(map);
                L.imageOverlay(url, [[-90, -540], [90, -180]], { opacity: 1 }).addTo(map);
            }
            function addSunMoonOverlay(map) {
                var now = Date.now();
                var sun = subsolarLonLat(now);
                var moon = sublunarLonLat(now);
                L.circleMarker([sun.lat, sun.lng], {
                    radius: 18,
                    fillColor: '#ffcc00',
                    color: 'none',
                    fillOpacity: 0.2,
                    weight: 0
                }).addTo(map);
                L.circleMarker([sun.lat, sun.lng], {
                    radius: 10,
                    fillColor: '#ffdd00',
                    color: '#cc9900',
                    weight: 2.5,
                    fillOpacity: 1
                }).addTo(map).bindTooltip('Sun', { permanent: false });
                L.circleMarker([moon.lat, moon.lng], {
                    radius: 14,
                    fillColor: '#e8e8f0',
                    color: 'none',
                    fillOpacity: 0.25,
                    weight: 0
                }).addTo(map);
                L.circleMarker([moon.lat, moon.lng], {
                    radius: 7,
                    fillColor: '#e8e8f0',
                    color: '#888',
                    weight: 2,
                    fillOpacity: 1
                }).addTo(map).bindTooltip('Moon', { permanent: false });
            }
            var AURORA_URL = 'https://services.swpc.noaa.gov/json/ovation_aurora_latest.json';
            function auroraRgb(val) {
                var t = Math.min(1, Math.max(0, val / 28));
                var r, g, b;
                if (t < 0.15) {
                    var u = t / 0.15;
                    r = Math.round(40 + u * 30);
                    g = Math.round(50 + u * 50);
                    b = Math.round(120 + u * 60);
                } else if (t < 0.35) {
                    var u = (t - 0.15) / 0.2;
                    r = Math.round(70 + u * 20);
                    g = Math.round(100 + u * 100);
                    b = Math.round(180 - u * 80);
                } else if (t < 0.55) {
                    var u = (t - 0.35) / 0.2;
                    r = Math.round(90 + u * 60);
                    g = Math.round(200 - u * 40);
                    b = Math.round(100 - u * 80);
                } else if (t < 0.75) {
                    var u = (t - 0.55) / 0.2;
                    r = Math.round(150 + u * 80);
                    g = Math.round(160 - u * 60);
                    b = Math.round(20 + u * 20);
                } else if (t < 0.9) {
                    var u = (t - 0.75) / 0.15;
                    r = Math.round(230);
                    g = Math.round(100 - u * 50);
                    b = Math.round(40);
                } else {
                    var u = (t - 0.9) / 0.1;
                    r = Math.round(255);
                    g = Math.round(50 - u * 30);
                    b = Math.round(40);
                }
                return [r, g, b];
            }
            function addAuroraOverlay(map, cfg) {
                var opacityPct = (cfg && cfg.aurora_opacity != null) ? Math.max(0, Math.min(100, cfg.aurora_opacity)) : 50;
                var opacityMult = opacityPct / 100;
                fetch(AURORA_URL).then(function(r) { return r.json(); }).then(function(data) {
                    var coords = data.coordinates;
                    if (!coords || !coords.length) return;
                    var threshold = 3;
                    var grid = [];
                    var lon, latIdx, val;
                    for (lon = 0; lon < 360; lon++) {
                        grid[lon] = [];
                        for (var li = 0; li <= 180; li++) grid[lon][li] = 0;
                    }
                    for (var i = 0; i < coords.length; i++) {
                        var c = coords[i];
                        lon = c[0];
                        var lat = c[1];
                        val = c[2];
                        if (lon >= 360) lon = 359;
                        latIdx = Math.round(lat + 90);
                        if (latIdx < 0) latIdx = 0;
                        if (latIdx > 180) latIdx = 180;
                        grid[lon][latIdx] = val;
                    }
                    for (lon = 0; lon < 360; lon++) {
                        grid[lon][0] = 0;
                        grid[lon][90] = 0;
                        grid[lon][180] = 0;
                    }
                    var w = 720;
                    var h = 362;
                    var canvas = document.createElement('canvas');
                    canvas.width = w;
                    canvas.height = h;
                    var ctx = canvas.getContext('2d');
                    var idata = ctx.createImageData(w, h);
                    var d = idata.data;
                    for (var y = 0; y < h; y++) {
                        latIdx = Math.min(180, Math.floor((h - 1 - y) * 181 / h));
                        for (var x = 0; x < w; x++) {
                            var lonIdx = Math.floor((x / w) * 360) % 360;
                            val = grid[lonIdx][latIdx];
                            var a = val >= threshold ? Math.round(255 * opacityMult) : 0;
                            var rgb = auroraRgb(val);
                            var i4 = (y * w + x) * 4;
                            d[i4] = rgb[0];
                            d[i4 + 1] = rgb[1];
                            d[i4 + 2] = rgb[2];
                            d[i4 + 3] = a;
                        }
                    }
                    ctx.putImageData(idata, 0, 0);
                    var url = canvas.toDataURL('image/png');
                    var bounds = [[-90, -180], [90, 180]];
                    L.imageOverlay(url, bounds, { opacity: 1 }).addTo(map);
                    L.imageOverlay(url, [[-90, 180], [90, 540]], { opacity: 1 }).addTo(map);
                    L.imageOverlay(url, [[-90, -540], [90, -180]], { opacity: 1 }).addTo(map);
                }).catch(function() {});
            }
            function applyOverlays(map, cfg) {
                if (cfg.grid_style && cfg.grid_style !== 'none') addGridOverlay(map, cfg.grid_style);
                if (cfg.show_terminator) addTerminatorOverlay(map);
                if (cfg.show_sun_moon) addSunMoonOverlay(map);
                if (cfg.show_aurora) addAuroraOverlay(map, cfg);
            }
            function syncMapSize(el) {
                if (!el._map) return;
                el._map.invalidateSize();
                var cell = el.closest('.grid-cell-map');
                if (!cell || el._map._userZoom == null) return;
                var vw = cell.clientWidth;
                var vh = cell.clientHeight;
                var cw = el.clientWidth;
                var ch = el.clientHeight;
                if (vw <= 0 || vh <= 0 || cw <= 0 || ch <= 0) return;
                if (cw > vw) {
                    var zoomAdj = Math.log(cw / vw) / Math.LN2;
                    var adjZoom = Math.max(0, Math.min(18, el._map._userZoom - zoomAdj));
                    el._map.setView(el._map.getCenter(), adjZoom);
                }
            }
            function initMaps() {
                document.querySelectorAll('.grid-cell-map .map_container').forEach(function(el) {
                    if (el._map) return;
                    var cfg = getMapSettings(el);
                    var zoom = cfg.zoom;
                    if (cfg.map_style === 'nasagibs' && zoom > 8) zoom = 8;
                    el._map = L.map(el, {
                        attributionControl: false,
                        zoomControl: false,
                        dragging: false,
                        scrollWheelZoom: false,
                        doubleClickZoom: false,
                        touchZoom: false,
                        boxZoom: false,
                        keyboard: false
                    });
                    el._map._userZoom = zoom;
                    el._map.setView([cfg.lat, cfg.lng], zoom);
                    getTileConfig(cfg.map_style, cfg.tile_style).addTo(el._map);
                    applyOverlays(el._map, cfg);
                    syncMapSize(el);
                    requestAnimationFrame(function() { syncMapSize(el); });
                    setTimeout(function() { syncMapSize(el); }, 0);
                    setTimeout(function() { syncMapSize(el); }, 150);
                    if (typeof ResizeObserver !== 'undefined') {
                        el._resizeObserver = new ResizeObserver(function() {
                            syncMapSize(el);
                        });
                        el._resizeObserver.observe(el);
                    }
                });
            }

            function loadLeafletAndInit() {
                var containers = document.querySelectorAll('.grid-cell-map .map_container');
                if (containers.length === 0) return;
                if (typeof L !== 'undefined') {
                    initMaps();
                    return;
                }
                var link = document.createElement('link');
                link.rel = 'stylesheet';
                link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
                document.head.appendChild(link);
                var script = document.createElement('script');
                script.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
                script.onload = initMaps;
                document.head.appendChild(script);
            }

            function runWhenReady() {
                function go() {
                    if (document.querySelectorAll('.grid-cell-map .map_container').length === 0) return;
                    if (document.readyState === 'complete') {
                        loadLeafletAndInit();
                    } else {
                        window.addEventListener('load', loadLeafletAndInit);
                    }
                }
                if (document.readyState === 'loading') {
                    document.addEventListener('DOMContentLoaded', go);
                } else {
                    go();
                }
            }
            runWhenReady();
        })();