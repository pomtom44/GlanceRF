(function() {
            var VALID_MAP_STYLES = ['carto', 'opentopomap', 'esri', 'nasagibs'];
            function getMapApiBase() {
                var mainPort = typeof window.GLANCERF_MAIN_PORT !== 'undefined' ? window.GLANCERF_MAIN_PORT : null;
                if (mainPort != null && String(location.port) !== String(mainPort)) {
                    return (location.protocol === 'https:' ? 'https://' : 'http://') + location.hostname + ':' + mainPort;
                }
                return '';
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
            function parseDmsCoord(str) {
                var dms = str.match(/^\s*(\d+)\s*[°º]\s*(\d+)\s*['′]\s*([\d.]+)\s*["″]?\s*([NSEW])/i);
                if (!dms) return null;
                var deg = parseInt(dms[1], 10);
                var min = parseInt(dms[2], 10);
                var sec = parseFloat(dms[3]);
                if (isNaN(sec)) sec = 0;
                var sign = (dms[4].toUpperCase() === 'S' || dms[4].toUpperCase() === 'W') ? -1 : 1;
                return sign * (deg + min / 60 + sec / 3600);
            }
            function parseCenter(centerStr, fallbackLat, fallbackLng) {
                var s = (centerStr || '').toString().trim();
                if (!s) return { lat: fallbackLat, lng: fallbackLng };
                var latLngMatch = s.match(/^\s*(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)\s*$/);
                if (latLngMatch) {
                    var la = parseFloat(latLngMatch[1]);
                    var lo = parseFloat(latLngMatch[2]);
                    if (!isNaN(la) && !isNaN(lo) && la >= -90 && la <= 90 && lo >= -180 && lo <= 180)
                        return { lat: la, lng: lo };
                }
                if (s.indexOf('°') >= 0 || s.indexOf('º') >= 0) {
                    var parts = s.split(/[\s,]+/).map(function(p) { return p.replace(/^[\s,]+|[\s,]+$/g, ''); }).filter(Boolean);
                    var latVal = null, lngVal = null;
                    for (var i = 0; i < parts.length; i++) {
                        var coord = parseDmsCoord(parts[i]);
                        if (coord !== null) {
                            if (parts[i].toUpperCase().indexOf('N') >= 0 || parts[i].toUpperCase().indexOf('S') >= 0) latVal = coord;
                            else if (parts[i].toUpperCase().indexOf('E') >= 0 || parts[i].toUpperCase().indexOf('W') >= 0) lngVal = coord;
                        }
                    }
                    if (latVal !== null && lngVal !== null && latVal >= -90 && latVal <= 90 && lngVal >= -180 && lngVal <= 180)
                        return { lat: latVal, lng: lngVal };
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
                var propagationSource = (ms.propagation_source && ms.propagation_source !== 'none') ? ms.propagation_source : 'none';
                var propagationOpacity = 60;
                if (ms.propagation_opacity !== undefined && ms.propagation_opacity !== '') {
                    var po = parseFloat(ms.propagation_opacity, 10);
                    if (!isNaN(po) && po >= 0 && po <= 100) propagationOpacity = po;
                }
                var propagationAprsHours = 6;
                if (ms.propagation_aprs_age !== undefined && ms.propagation_aprs_age !== '') {
                    var ageStr = String(ms.propagation_aprs_age).trim();
                    var parts = ageStr.split(':');
                    if (parts.length === 2) {
                        var hrs = parseInt(parts[0], 10);
                        var mins = parseInt(parts[1], 10);
                        if (!isNaN(hrs) && !isNaN(mins) && mins >= 0 && mins < 60) {
                            var h = hrs + mins / 60;
                            if (h > 0) propagationAprsHours = Math.max(0.25, Math.min(168, h));
                        }
                    } else if (parts.length === 1 && ageStr !== '') {
                        var h = parseFloat(ageStr, 10);
                        if (!isNaN(h) && h > 0) propagationAprsHours = Math.max(0.25, Math.min(168, h));
                    }
                } else if (ms.propagation_aprs_hours && ['1','6','12','24'].indexOf(String(ms.propagation_aprs_hours)) >= 0) {
                    propagationAprsHours = parseFloat(ms.propagation_aprs_hours, 10);
                }
                return { zoom: zoom, lat: lat, lng: lng, map_style: mapStyle, tile_style: tileStyle, grid_style: gridStyle, show_terminator: showTerminator, show_sun_moon: showSunMoon, show_aurora: showAurora, aurora_opacity: auroraOpacity, propagation_source: propagationSource, propagation_opacity: propagationOpacity, propagation_aprs_hours: propagationAprsHours };
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
            /* Sublunar point: geocentric moon position converted to geographic lat/lng.
             * Uses formulas from aa.quae.nl / suncalc (Meeus-based) to match timeanddate.com. */
            function sublunarLonLat(now) {
                var rad = Math.PI / 180;
                var jd = (now / 86400000) - 0.5 + 2440588;
                var d = jd - 2451545;
                var L = rad * (218.316 + 13.176396 * d);
                var M = rad * (134.963 + 13.064993 * d);
                var F = rad * (93.272 + 13.229350 * d);
                var D = rad * (297.850 + 12.190749 * d);
                var l = L + rad * (6.289 * Math.sin(M) + 1.274 * Math.sin(2 * D - M) + 0.658 * Math.sin(2 * D));
                var b = rad * 5.128 * Math.sin(F);
                var e = rad * 23.4397;
                var ra = Math.atan2(Math.sin(l) * Math.cos(e) - Math.tan(b) * Math.sin(e), Math.cos(l));
                var dec = Math.asin(Math.max(-1, Math.min(1, Math.sin(b) * Math.cos(e) + Math.cos(b) * Math.sin(e) * Math.sin(l))));
                var gmstDeg = ((280.16 + 360.9856235 * d) % 360 + 360) % 360;
                var lon = (ra / rad) - gmstDeg;
                while (lon > 180) lon -= 360;
                while (lon < -180) lon += 360;
                return { lat: dec / rad, lng: lon };
            }
            /* Day/night terminator with twilight zones (inspired by timeanddate.com sunearth map).
             * angleDeg = angular distance from point to subsolar point. 90° = terminator (sun on horizon).
             * Twilight zones: civil 0–6° below, nautical 6–12°, astronomical 12–18°, night >18°. */
            function addTerminatorOverlay(map) {
                var now = Date.now();
                var sub = subsolarLonLat(now);
                var decRad = sub.lat * Math.PI / 180;
                var w = 1440;
                var h = 724;
                var canvas = document.createElement('canvas');
                canvas.width = w;
                canvas.height = h;
                var ctx = canvas.getContext('2d');
                var idata = ctx.createImageData(w, h);
                var d = idata.data;
                var sinDec = Math.sin(decRad);
                var cosDec = Math.cos(decRad);
                for (var y = 0; y < h; y++) {
                    var lat = 90 - ((y + 0.5) / h) * 180;
                    var latRad = lat * Math.PI / 180;
                    var sinLat = Math.sin(latRad);
                    var cosLat = Math.cos(latRad);
                    for (var x = 0; x < w; x++) {
                        var lon = -180 + ((x + 0.5) / w) * 360;
                        var lonDiffRad = (lon - sub.lng) * Math.PI / 180;
                        var cosAngle = sinLat * sinDec + cosLat * cosDec * Math.cos(lonDiffRad);
                        var angleRad = Math.acos(Math.max(-1, Math.min(1, cosAngle)));
                        var angleDeg = angleRad * 180 / Math.PI;
                        var nightAlpha = 0;
                        if (angleDeg >= 108) {
                            nightAlpha = 0.58;
                        } else if (angleDeg >= 102) {
                            nightAlpha = 0.42 + 0.16 * (angleDeg - 102) / 6;
                        } else if (angleDeg >= 96) {
                            nightAlpha = 0.26 + 0.16 * (angleDeg - 96) / 6;
                        } else if (angleDeg >= 90) {
                            nightAlpha = 0.10 + 0.16 * (angleDeg - 90) / 6;
                        }
                        var i4 = (y * w + x) * 4;
                        d[i4] = 8;
                        d[i4 + 1] = 12;
                        d[i4 + 2] = 28;
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
            var PROPAGATION_DATA_SOURCES = ['kc2g_muf', 'kc2g_fof2', 'tropo', 'vhf_aprs'];
            var PROPAGATION_SOURCES = [
                { id: 'kc2g_muf', url: 'https://prop.kc2g.com/renders/current/mufd-normal-now.svg', bounds: [[-90, -180], [90, 180]], cacheBust: true },
                { id: 'kc2g_fof2', url: 'https://prop.kc2g.com/renders/current/fof2-normal-now.svg', bounds: [[-90, -180], [90, 180]], cacheBust: true }
            ];
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
            function propagationRgb(t) {
                var r, g, b;
                if (t < 0.2) {
                    var u = t / 0.2;
                    r = Math.round(20 + u * 60);
                    g = Math.round(40 + u * 80);
                    b = Math.round(140 + u * 60);
                } else if (t < 0.45) {
                    var u = (t - 0.2) / 0.25;
                    r = Math.round(80 + u * 40);
                    g = Math.round(120 + u * 100);
                    b = Math.round(200 - u * 120);
                } else if (t < 0.7) {
                    var u = (t - 0.45) / 0.25;
                    r = Math.round(120 + u * 100);
                    g = Math.round(220 - u * 80);
                    b = Math.round(80 - u * 80);
                } else {
                    var u = (t - 0.7) / 0.3;
                    r = Math.round(220 + u * 35);
                    g = Math.round(140 - u * 100);
                    b = Math.round(20);
                }
                return [Math.min(255, r), Math.min(255, g), Math.min(255, b)];
            }
            function vhfPropagationRgb(t) {
                var r, g, b;
                if (t < 0.25) {
                    var u = t / 0.25;
                    r = Math.round(34 + u * 70);
                    g = Math.round(139 + u * 80);
                    b = Math.round(34);
                } else if (t < 0.5) {
                    var u = (t - 0.25) / 0.25;
                    r = Math.round(104 + u * 120);
                    g = Math.round(219 - u * 19);
                    b = Math.round(34);
                } else if (t < 0.75) {
                    var u = (t - 0.5) / 0.25;
                    r = Math.round(224 + u * 31);
                    g = Math.round(200 - u * 80);
                    b = Math.round(34);
                } else {
                    var u = (t - 0.75) / 0.25;
                    r = Math.round(255);
                    g = Math.round(120 - u * 120);
                    b = Math.round(34);
                }
                return [Math.min(255, r), Math.min(255, g), Math.min(255, b)];
            }
            function idwGrid(coords, w, h, power) {
                power = power || 2;
                var grid = [];
                var x, y, lon, lat, i, d, weight, sumW, sumV;
                for (y = 0; y < h; y++) {
                    grid[y] = [];
                    lat = 90 - ((y + 0.5) / h) * 180;
                    for (x = 0; x < w; x++) {
                        lon = -180 + ((x + 0.5) / w) * 360;
                        sumW = 0;
                        sumV = 0;
                        for (i = 0; i < coords.length; i++) {
                            d = Math.sqrt(Math.pow(lon - coords[i][0], 2) + Math.pow(lat - coords[i][1], 2));
                            d = Math.max(0.5, d);
                            weight = 1 / Math.pow(d, power);
                            sumW += weight;
                            sumV += weight * coords[i][2];
                        }
                        grid[y][x] = sumW > 0 ? sumV / sumW : 0;
                    }
                }
                return grid;
            }
            var VIEWPORT_BUFFER = 0.25;
            function getBoundsWithBuffer(map) {
                var b = map.getBounds();
                if (!b || !b.pad) return b;
                return b.pad(VIEWPORT_BUFFER);
            }
            function blobBoundsIntersectsViewport(hull, paddedBounds) {
                if (!hull || hull.length < 2 || !paddedBounds) return false;
                var minLat = hull[0][0], maxLat = hull[0][0], minLon = hull[0][1], maxLon = hull[0][1];
                for (var i = 1; i < hull.length; i++) {
                    var lat = hull[i][0], lon = hull[i][1];
                    if (lat < minLat) minLat = lat;
                    if (lat > maxLat) maxLat = lat;
                    if (lon < minLon) minLon = lon;
                    if (lon > maxLon) maxLon = lon;
                }
                var blobBounds = L.latLngBounds([minLat, minLon], [maxLat, maxLon]);
                return paddedBounds.intersects(blobBounds);
            }
            function addPropagationDataOverlay(map, cfg, sourceId) {
                var layerGroup = map._propagationLayerGroup;
                if (!layerGroup) {
                    layerGroup = L.layerGroup();
                    map._propagationLayerGroup = layerGroup;
                    layerGroup.addTo(map);
                }
                layerGroup.clearLayers();
                var opacityPct = (cfg && cfg.propagation_opacity != null) ? Math.max(0, Math.min(100, cfg.propagation_opacity)) : 60;
                var opacityMult = opacityPct / 100;
                var valMin, valMax;
                if (sourceId === 'kc2g_muf') { valMin = 5; valMax = 30; }
                else if (sourceId === 'kc2g_fof2') { valMin = 2; valMax = 12; }
                else if (sourceId === 'tropo') { valMin = 200; valMax = 450; }
                else if (sourceId === 'vhf_aprs') { valMin = 15; valMax = 800; }
                else { valMin = 0; valMax = 1; }
                var url = getMapApiBase() + '/api/map/propagation-data?source=' + encodeURIComponent(sourceId);
                if (sourceId === 'vhf_aprs' && cfg && cfg.propagation_aprs_hours) {
                    url += '&hours=' + encodeURIComponent(cfg.propagation_aprs_hours);
                }
                fetch(url).then(function(r) {
                    if (!r.ok) return {};
                    return r.json();
                }).then(function(data) {
                    var coords = data && data.coordinates;
                    if (sourceId === 'vhf_aprs' && data.blobs && data.blobs.length > 0) {
                        var paddedBounds = getBoundsWithBuffer(map);
                        var opacity = Math.max(0.35, Math.min(0.7, opacityMult));
                        function chaikinSmooth(pts, passes) {
                            passes = passes || 1;
                            var i, j, p, q, n;
                            for (j = 0; j < passes; j++) {
                                n = pts.length;
                                var out = [];
                                for (i = 0; i < n; i++) {
                                    p = pts[i];
                                    q = pts[(i + 1) % n];
                                    out.push([0.75 * p[0] + 0.25 * q[0], 0.75 * p[1] + 0.25 * q[1]]);
                                    out.push([0.25 * p[0] + 0.75 * q[0], 0.25 * p[1] + 0.75 * q[1]]);
                                }
                                pts = out;
                            }
                            return pts;
                        }
                        var blobsList = [];
                        for (var bi = 0; bi < data.blobs.length; bi++) {
                            var blob = data.blobs[bi];
                            var hull = blob.hull;
                            if (!hull || hull.length < 3) continue;
                            if (paddedBounds && !blobBoundsIntersectsViewport(hull, paddedBounds)) continue;
                            var maxDist = blob.maxDist != null ? blob.maxDist : 200;
                            if (maxDist < valMin || maxDist > valMax) continue;
                            blobsList.push({ blob: blob, maxDist: maxDist });
                        }
                        blobsList.sort(function(a, b) { return a.maxDist - b.maxDist; });
                        for (var b = 0; b < blobsList.length; b++) {
                            var blob = blobsList[b].blob;
                            var hull = blob.hull;
                            var maxDist = blob.maxDist != null ? blob.maxDist : 200;
                            var t = (maxDist - valMin) / (valMax - valMin);
                            var rgb = vhfPropagationRgb(t);
                            var color = 'rgb(' + rgb[0] + ',' + rgb[1] + ',' + rgb[2] + ')';
                            var smoothed = chaikinSmooth(hull, 3);
                            L.polygon(smoothed, {
                                color: color,
                                weight: 0.5,
                                opacity: 0.6,
                                fillColor: color,
                                fillOpacity: opacity
                            }).addTo(layerGroup);
                        }
                        return;
                    }
                    if (sourceId === 'vhf_aprs' && coords && coords.length >= 2) {
                        var w = 720;
                        var h = 362;
                        var grid = idwGrid(coords, w, h, 2);
                        var canvas = document.createElement('canvas');
                        canvas.width = w;
                        canvas.height = h;
                        var ctx = canvas.getContext('2d');
                        var idata = ctx.createImageData(w, h);
                        var d = idata.data;
                        var val, t, rgb, a, i4;
                        for (var y = 0; y < h; y++) {
                            for (var x = 0; x < w; x++) {
                                val = grid[y][x];
                                if (val < valMin || val > valMax) {
                                    rgb = null;
                                    a = 0;
                                } else {
                                    t = (val - valMin) / (valMax - valMin);
                                    rgb = propagationRgb(t);
                                    a = Math.round(200 * opacityMult);
                                }
                                i4 = (y * w + x) * 4;
                                d[i4] = rgb ? rgb[0] : 0;
                                d[i4 + 1] = rgb ? rgb[1] : 0;
                                d[i4 + 2] = rgb ? rgb[2] : 0;
                                d[i4 + 3] = a;
                            }
                        }
                        ctx.putImageData(idata, 0, 0);
                        var imgUrl = canvas.toDataURL('image/png');
                        var bounds = [[-90, -180], [90, 180]];
                        L.imageOverlay(imgUrl, bounds, { opacity: 1 }).addTo(layerGroup);
                        L.imageOverlay(imgUrl, [[-90, 180], [90, 540]], { opacity: 1 }).addTo(layerGroup);
                        L.imageOverlay(imgUrl, [[-90, -540], [90, -180]], { opacity: 1 }).addTo(layerGroup);
                        return;
                    }
                    if (!coords || coords.length < 2) {
                        return;
                    }
                    var w = 720;
                    var h = 362;
                    var grid = idwGrid(coords, w, h, 2);
                    var canvas = document.createElement('canvas');
                    canvas.width = w;
                    canvas.height = h;
                    var ctx = canvas.getContext('2d');
                    var idata = ctx.createImageData(w, h);
                    var d = idata.data;
                    var val, t, rgb, a, i4;
                    for (var y = 0; y < h; y++) {
                        for (var x = 0; x < w; x++) {
                            val = grid[y][x];
                            if (val < valMin || val > valMax) {
                                rgb = null;
                                a = 0;
                            } else {
                                t = (val - valMin) / (valMax - valMin);
                                rgb = propagationRgb(t);
                                a = Math.round(200 * opacityMult);
                            }
                            i4 = (y * w + x) * 4;
                            d[i4] = rgb ? rgb[0] : 0;
                            d[i4 + 1] = rgb ? rgb[1] : 0;
                            d[i4 + 2] = rgb ? rgb[2] : 0;
                            d[i4 + 3] = a;
                        }
                    }
                    ctx.putImageData(idata, 0, 0);
                    var url = canvas.toDataURL('image/png');
                    var bounds = [[-90, -180], [90, 180]];
                    L.imageOverlay(url, bounds, { opacity: 1 }).addTo(layerGroup);
                    L.imageOverlay(url, [[-90, 180], [90, 540]], { opacity: 1 }).addTo(layerGroup);
                    L.imageOverlay(url, [[-90, -540], [90, -180]], { opacity: 1 }).addTo(layerGroup);
                }).catch(function() {});
            }
            function addPropagationImageOverlay(map, cfg, sourceId) {
                var spec = null;
                for (var i = 0; i < PROPAGATION_SOURCES.length; i++) {
                    if (PROPAGATION_SOURCES[i].id === sourceId) { spec = PROPAGATION_SOURCES[i]; break; }
                }
                if (!spec) return;
                var opacityPct = (cfg && cfg.propagation_opacity != null) ? Math.max(0, Math.min(100, cfg.propagation_opacity)) : 60;
                var opacity = opacityPct / 100;
                var url = spec.url;
                if (spec.cacheBust) {
                    var t = Math.floor(Date.now() / 900000) * 900000;
                    url = url + (url.indexOf('?') >= 0 ? '&' : '?') + 't=' + t;
                }
                var bounds = spec.bounds || [[-90, -180], [90, 180]];
                var layerGroup = map._propagationLayerGroup;
                if (!layerGroup) {
                    layerGroup = L.layerGroup();
                    map._propagationLayerGroup = layerGroup;
                    layerGroup.addTo(map);
                }
                layerGroup.clearLayers();
                var overlay = L.imageOverlay(url, bounds, { opacity: opacity });
                overlay.addTo(layerGroup);
                overlay.on('error', function() { overlay.remove(); });
            }
            function addAuroraOverlay(map, cfg) {
                var layerGroup = map._auroraLayerGroup;
                if (!layerGroup) {
                    layerGroup = L.layerGroup();
                    map._auroraLayerGroup = layerGroup;
                    layerGroup.addTo(map);
                }
                layerGroup.clearLayers();
                var opacityPct = (cfg && cfg.aurora_opacity != null) ? Math.max(0, Math.min(100, cfg.aurora_opacity)) : 50;
                var opacityMult = opacityPct / 100;
                var url = getMapApiBase() + '/api/map/aurora-data';
                fetch(url).then(function(r) {
                    if (!r.ok) return null;
                    return r.json();
                }).then(function(data) {
                    if (!data) return;
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
                        if (Math.abs(lat) < 20) continue;
                        if (lon >= 360) lon = 359;
                        latIdx = Math.round(lat + 90);
                        if (latIdx < 0) latIdx = 0;
                        if (latIdx > 180) latIdx = 180;
                        grid[lon][latIdx] = val;
                    }
                    for (lon = 0; lon < 360; lon++) {
                        grid[lon][0] = 0;
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
                            var lonDeg = -180 + (x / w) * 360;
                            var lonIdx = Math.min(359, Math.floor((lonDeg + 360) % 360));
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
                    var imgUrl = canvas.toDataURL('image/png');
                    var bounds = [[-90, -180], [90, 180]];
                    L.imageOverlay(imgUrl, bounds, { opacity: 1 }).addTo(layerGroup);
                    L.imageOverlay(imgUrl, [[-90, 180], [90, 540]], { opacity: 1 }).addTo(layerGroup);
                    L.imageOverlay(imgUrl, [[-90, -540], [90, -180]], { opacity: 1 }).addTo(layerGroup);
                }).catch(function() {});
            }
            var PROPAGATION_REFRESH_MS = 5 * 60 * 1000;
            function addPropagationOverlay(map, cfg) {
                var sourceId = (cfg && cfg.propagation_source) ? cfg.propagation_source : 'none';
                if (!sourceId || sourceId === 'none') return;
                if (!map._propagationLayerGroup) {
                    map._propagationLayerGroup = L.layerGroup();
                    map._propagationLayerGroup.addTo(map);
                }
                map._propagationLayerGroup.clearLayers();
                if (PROPAGATION_DATA_SOURCES.indexOf(sourceId) >= 0) {
                    addPropagationDataOverlay(map, cfg, sourceId);
                    return;
                }
                var spec = null;
                for (var i = 0; i < PROPAGATION_SOURCES.length; i++) {
                    if (PROPAGATION_SOURCES[i].id === sourceId) { spec = PROPAGATION_SOURCES[i]; break; }
                }
                if (!spec) return;
                addPropagationImageOverlay(map, cfg, sourceId);
            }
            function aprsAgeToRgb(ageHours, maxAgeHours) {
                if (maxAgeHours <= 0) return [46, 204, 113];
                var t = Math.min(1, Math.max(0, ageHours / maxAgeHours));
                var r = Math.round(46 + t * (231 - 46));
                var g = Math.round(204 + t * (76 - 204));
                var b = Math.round(113 + t * (60 - 113));
                return [r, g, b];
            }
            var APRS_SYMBOL_SIZE = 32;
            var APRS_SPRITE_BASE = 'https://cdn.jsdelivr.net/gh/hessu/aprs-symbols@master/png';
            function getAprsSymbolDivIcon(symbolTable, symbol, anchorBottomCenter) {
                var tableIdx = (symbolTable === '\\' || symbolTable === '\u005C') ? 1 : 0;
                var code = (symbol && symbol.length) ? symbol.charCodeAt(0) : 63;
                code = Math.max(33, Math.min(127, code));
                var index = code - 33;
                var row = Math.floor(index / 16);
                var col = index % 16;
                var cell = APRS_SYMBOL_SIZE;
                var posX = -col * cell;
                var posY = -row * cell;
                var spriteUrl = APRS_SPRITE_BASE + '/aprs-symbols-' + cell + '-' + tableIdx + '.png';
                var aprsCode = (symbolTable || '/') + (symbol || '?');
                var aprsCodeEsc = aprsCode.replace(/&/g, '&amp;').replace(/"/g, '&quot;');
                var html = '<div class="aprs-symbol-cell" style="width:' + cell + 'px;height:' + cell + 'px;background:url(\'' + spriteUrl + '\') ' + posX + 'px ' + posY + 'px no-repeat;" data-aprs-code="' + aprsCodeEsc + '" title="APRS ' + aprsCodeEsc + '"><span class="aprs-symbol-code-debug" aria-hidden="true" style="position:absolute;left:-9999px;width:1px;height:1px;overflow:hidden;">' + aprsCodeEsc + '</span></div>';
                var anchor = anchorBottomCenter ? [cell / 2, cell] : [cell / 2, cell / 2];
                return L.divIcon({
                    html: html,
                    className: 'aprs-symbol-icon-wrap',
                    iconSize: [cell, cell],
                    iconAnchor: anchor
                });
            }
            function getQthFromCallsignModule() {
                var allSettings = window.GLANCERF_MODULE_SETTINGS || {};
                var cells = document.querySelectorAll('.grid-cell-callsign');
                for (var i = 0; i < cells.length; i++) {
                    var cell = cells[i];
                    var r = cell.getAttribute('data-row');
                    var c = cell.getAttribute('data-col');
                    if (r == null || c == null) continue;
                    var key = r + '_' + c;
                    var ms = allSettings[key];
                    if (!ms) continue;
                    if (ms.show_qth_on_map !== '1' && ms.show_qth_on_map !== true) continue;
                    var grid = (ms.grid || window.GLANCERF_SETUP_LOCATION || '').toString().trim();
                    if (!grid) continue;
                    var latLng = maidenheadToLatLng(grid);
                    if (!latLng) continue;
                    var callsign = (ms.callsign || window.GLANCERF_SETUP_CALLSIGN || '').toString().trim() || 'QTH';
                    var iconVal = (ms.qth_map_icon != null && ms.qth_map_icon !== '') ? String(ms.qth_map_icon).trim() : '/-';
                    if (iconVal.length === 0) iconVal = '/-';
                    var symbolTable = iconVal.charAt(0) || '/';
                    var symbol = iconVal.length >= 2 ? iconVal.charAt(1) : (iconVal.charAt(0) || '[');
                    return { lat: latLng.lat, lng: latLng.lng, callsign: callsign, symbolTable: symbolTable, symbol: symbol };
                }
                return null;
            }
            function addQthMarkerOverlay(map) {
                var layerGroup = map._qthMarkerLayerGroup;
                if (!layerGroup) {
                    layerGroup = L.layerGroup();
                    map._qthMarkerLayerGroup = layerGroup;
                    layerGroup.addTo(map);
                }
                layerGroup.clearLayers();
                var qth = getQthFromCallsignModule();
                if (!qth || typeof L === 'undefined') return;
                var icon = getAprsSymbolDivIcon(qth.symbolTable, qth.symbol, false);
                var m = L.marker([qth.lat, qth.lng], { icon: icon });
                if (qth.callsign) m.bindTooltip(qth.callsign, { permanent: false, direction: 'top', offset: [0, -16] });
                m.addTo(layerGroup);
            }
            function parseNoradIdList(raw) {
                var list = [];
                if (raw == null || (typeof raw === 'string' && !raw.trim())) return list;
                try {
                    if (typeof raw === 'string') {
                        var trimmed = raw.trim();
                        if (trimmed.indexOf('[') === 0) list = JSON.parse(trimmed);
                        else list = trimmed.split(',').map(function(s) { return parseInt(s.trim(), 10); }).filter(function(n) { return !isNaN(n); });
                    } else if (Array.isArray(raw)) list = raw;
                } catch (e) {}
                return list;
            }
            function addAprsLocationsOverlay(map, cfg) {
                var layerGroup = map._aprsLocationsLayerGroup;
                if (!layerGroup) {
                    layerGroup = L.layerGroup();
                    map._aprsLocationsLayerGroup = layerGroup;
                    layerGroup.addTo(map);
                }
                layerGroup.clearLayers();
                var ms = getMergedModuleSettings('aprs');
                var hours = (cfg && cfg.propagation_aprs_hours) ? cfg.propagation_aprs_hours : 6;
                if (ms.hours != null && ms.hours !== '') {
                    var h = parseFloat(ms.hours, 10);
                    if (!isNaN(h) && h > 0 && h <= 168) hours = h;
                }
                var displayMode = (ms.aprs_display_mode === 'icons') ? 'icons' : 'dots';
                var aprsFilter = (ms.aprs_filter != null && typeof ms.aprs_filter === 'string') ? ms.aprs_filter.trim() : '';
                var ageLimitHours = typeof hours === 'number' ? hours : parseFloat(hours, 10) || 6;
                var url = getMapApiBase() + '/api/map/aprs-locations?hours=' + encodeURIComponent(hours);
                if (aprsFilter) url += '&filter=' + encodeURIComponent(aprsFilter);
                fetch(url).then(function(r) {
                    if (!r.ok) return { locations: [] };
                    return r.json();
                }).then(function(data) {
                    var locs = data && data.locations;
                    if (!locs || !locs.length) return;
                    if (!locs.length) return;
                    var paddedBounds = getBoundsWithBuffer(map);
                    var nowSec = Date.now() / 1000;
                    for (var i = 0; i < locs.length; i++) {
                        var loc = locs[i];
                        var lat = loc.lat, lon = loc.lon, callsign = loc.callsign || '';
                        if (paddedBounds && !paddedBounds.contains([lat, lon])) continue;
                        var lastSeen = loc.lastSeen;
                        var ageHours = lastSeen != null ? (nowSec - lastSeen) / 3600 : 0;
                        if (ageHours >= ageLimitHours) continue;
                        if (displayMode === 'icons') {
                            var table = loc.symbolTable || '/';
                            var sym = loc.symbol || '?';
                            var icon = getAprsSymbolDivIcon(table, sym);
                            var m = L.marker([lat, lon], { icon: icon });
                            if (callsign) m.bindTooltip(callsign, { permanent: false, direction: 'top', offset: [0, -16] });
                            m.addTo(layerGroup);
                        } else {
                            var rgb = aprsAgeToRgb(ageHours, ageLimitHours);
                            var fillColor = 'rgb(' + rgb[0] + ',' + rgb[1] + ',' + rgb[2] + ')';
                            var m = L.circleMarker([lat, lon], {
                                radius: 4,
                                fillColor: fillColor,
                                color: '#1a1a1a',
                                weight: 1,
                                opacity: 0.9,
                                fillOpacity: 0.85
                            });
                            if (callsign) m.bindTooltip(callsign, { permanent: false, direction: 'top', offset: [0, -4] });
                            m.addTo(layerGroup);
                        }
                    }
                }).catch(function() {});
            }
            var LIVE_SPOTS_BANDS = [
                { id: '160', minKHz: 1800, maxKHz: 2000 }, { id: '80', minKHz: 3500, maxKHz: 4000 },
                { id: '60', minKHz: 5300, maxKHz: 5400 }, { id: '40', minKHz: 7000, maxKHz: 7300 },
                { id: '30', minKHz: 10100, maxKHz: 10150 }, { id: '20', minKHz: 14000, maxKHz: 14350 },
                { id: '17', minKHz: 18068, maxKHz: 18168 }, { id: '15', minKHz: 21000, maxKHz: 21450 },
                { id: '12', minKHz: 24890, maxKHz: 24990 }, { id: '10', minKHz: 28000, maxKHz: 29700 },
                { id: '6', minKHz: 50000, maxKHz: 54000 }, { id: '2', minKHz: 144000, maxKHz: 148000 }
            ];
            var LIVE_SPOTS_DEFAULT_COLORS = { '160': '#8b4513', '80': '#4682b4', '60': '#20b2aa', '40': '#00ff00', '30': '#9acd32', '20': '#ffd700', '17': '#ff8c00', '15': '#f08080', '12': '#da70d6', '10': '#9370db', '6': '#00ced1', '2': '#e0e0e0' };
            function liveSpotsFreqToBand(khz) {
                if (khz == null || isNaN(khz)) return null;
                var k = parseInt(khz, 10);
                for (var i = 0; i < LIVE_SPOTS_BANDS.length; i++) {
                    if (k >= LIVE_SPOTS_BANDS[i].minKHz && k <= LIVE_SPOTS_BANDS[i].maxKHz) return LIVE_SPOTS_BANDS[i].id;
                }
                return null;
            }
            function liveSpotsGetBandColor(settings, bandId) {
                if (!bandId) return '#888';
                var key = 'band_' + bandId + '_color';
                var c = settings && (settings[key] !== undefined && settings[key] !== null && settings[key] !== '') ? String(settings[key]).trim() : null;
                if (c && /^#[0-9A-Fa-f]{3,8}$/.test(c)) return c;
                return LIVE_SPOTS_DEFAULT_COLORS[bandId] || '#888';
            }
            function liveSpotsIsBandEnabled(settings, bandId) {
                if (!settings) return true;
                var key = 'band_' + bandId;
                var v = settings[key];
                if (v === false || v === 'false' || v === '0' || v === 0) return false;
                return true;
            }
            function greatCirclePoints(lat1, lon1, lat2, lon2, numPoints) {
                var toRad = Math.PI / 180;
                var lat1r = lat1 * toRad, lon1r = lon1 * toRad;
                var lat2r = lat2 * toRad, lon2r = lon2 * toRad;
                var x1 = Math.cos(lat1r) * Math.cos(lon1r);
                var y1 = Math.cos(lat1r) * Math.sin(lon1r);
                var z1 = Math.sin(lat1r);
                var x2 = Math.cos(lat2r) * Math.cos(lon2r);
                var y2 = Math.cos(lat2r) * Math.sin(lon2r);
                var z2 = Math.sin(lat2r);
                var dot = x1 * x2 + y1 * y2 + z1 * z2;
                if (dot > 1) dot = 1;
                if (dot < -1) dot = -1;
                var omega = Math.acos(dot);
                if (omega < 1e-6) return [[lat1, lon1], [lat2, lon2]];
                var pts = [];
                for (var i = 0; i <= numPoints; i++) {
                    var t = i / numPoints;
                    var a = Math.sin((1 - t) * omega) / Math.sin(omega);
                    var b = Math.sin(t * omega) / Math.sin(omega);
                    var x = a * x1 + b * x2;
                    var y = a * y1 + b * y2;
                    var z = a * z1 + b * z2;
                    var lat = Math.atan2(z, Math.sqrt(x * x + y * y)) / toRad;
                    var lon = Math.atan2(y, x) / toRad;
                    pts.push([lat, lon]);
                }
                return pts;
            }
            function addLiveSpotsLinesOverlay(map) {
                if (typeof L === 'undefined') return;
                if (!hasMapOverlayForModule('live_spots')) {
                    if (map._liveSpotsLinesLayerGroup) {
                        map.removeLayer(map._liveSpotsLinesLayerGroup);
                        map._liveSpotsLinesLayerGroup = null;
                    }
                    return;
                }
                var ms = getMergedModuleSettings('live_spots');
                var callsignOrGrid = (ms.callsign_or_grid || '').toString().trim();
                if (!callsignOrGrid) return;
                var layerGroup = map._liveSpotsLinesLayerGroup;
                if (!layerGroup) {
                    layerGroup = L.layerGroup();
                    map._liveSpotsLinesLayerGroup = layerGroup;
                    layerGroup.addTo(map);
                }
                layerGroup.clearLayers();
                var filterMode = (ms.filter_mode || 'received').toString().trim().toLowerCase();
                var ageMins = parseInt(ms.age_mins, 10);
                if (isNaN(ageMins) || ageMins < 1) ageMins = 60;
                var setupLoc = (window.GLANCERF_SETUP_LOCATION || '').toString().trim();
                var qthStr = setupLoc || callsignOrGrid;
                var qth = parseCenter(qthStr, 0, 0);
                if (!qth || (qth.lat === 0 && qth.lng === 0 && !qthStr)) return;
                var url = getMapApiBase() + '/api/live_spots/spots?filter_mode=' + encodeURIComponent(filterMode) +
                    '&callsign_or_grid=' + encodeURIComponent(callsignOrGrid) + '&age_mins=' + ageMins;
                fetch(url).then(function(r) {
                    if (!r.ok) return { spots: [] };
                    return r.json();
                }).then(function(data) {
                    var spots = (data && data.spots) ? data.spots : [];
                    if (!spots.length) return;
                    for (var i = 0; i < spots.length; i++) {
                        var s = spots[i];
                        var remoteLoc = (filterMode === 'sent')
                            ? (s.receiverLocator || s.receiver_locator || s.rl)
                            : (s.senderLocator || s.sender_locator || s.sl);
                        if (!remoteLoc || (remoteLoc + '').trim().length < 2) continue;
                        var remote = maidenheadToLatLng(remoteLoc);
                        if (!remote) continue;
                        var khz = (s.frequency && !isNaN(Number(s.frequency))) ? Number(s.frequency) / 1000 : null;
                        var bandId = liveSpotsFreqToBand(khz);
                        if (!liveSpotsIsBandEnabled(ms, bandId || '20')) continue;
                        var color = liveSpotsGetBandColor(ms, bandId || '20');
                        var pts = greatCirclePoints(qth.lat, qth.lng, remote.lat, remote.lng, 24);
                        var segs = splitPathAtWrapBoundaries(pts);
                        if (segs.length === 0) segs = [pts];
                        segs.forEach(function(seg) {
                            if (seg.length < 2) return;
                            var linePts = seg.map(function(p) { return [p[0], p[1]]; });
                            L.polyline(linePts, { color: color, weight: 2, opacity: 0.6, smoothFactor: 1 }).addTo(layerGroup);
                        });
                    }
                    if (map.hasLayer(layerGroup)) layerGroup.bringToFront();
                }).catch(function() {});
            }
            /* sat_new: uses /api/satellite/locations (same cache as satellite_pass overlay).
               We only fetch and display sat_new locations when the map module is loaded (this script
               runs only when map is in the layout and there are .grid-cell-map .map_container elements). */
            function addSatNewLocationsOverlay(map) {
                if (typeof L === 'undefined') return;
                var layerGroup = map._satNewLocationsLayerGroup;
                if (!layerGroup) {
                    layerGroup = L.layerGroup();
                    map._satNewLocationsLayerGroup = layerGroup;
                    layerGroup.addTo(map);
                }
                var url = getMapApiBase() + '/api/satellite/locations';
                fetch(url).then(function(r) {
                    if (!r.ok) return { positions: {} };
                    return r.json();
                }).then(function(data) {
                    var positions = (data && data.positions) ? data.positions : {};
                    var locs = Object.keys(positions).map(function(norad) {
                        var ll = positions[norad];
                        return Array.isArray(ll) && ll.length >= 2 ? { lat: ll[0], lon: ll[1] } : null;
                    }).filter(Boolean);
                    layerGroup.clearLayers();
                    if (!map.hasLayer(layerGroup)) layerGroup.addTo(map);
                    for (var i = 0; i < locs.length; i++) {
                        var loc = locs[i];
                        var lat = loc.lat != null ? Number(loc.lat) : NaN;
                        var lon = loc.lon != null ? Number(loc.lon) : NaN;
                        if (!isNaN(lat) && !isNaN(lon)) {
                            L.circleMarker([lat, lon], {
                                radius: 4,
                                fillColor: '#00b4ff',
                                color: '#fff',
                                weight: 1,
                                fillOpacity: 0.9
                            }).addTo(layerGroup);
                        }
                    }
                    layerGroup.bringToFront();
                }).catch(function() {});
            }
            /* Satellite-pass position logic (confirm):
             * 1. Get "current" position, velocity (deg/s), and per-NORAD position_updated_utc from cache via /api/satellite/locations. Backend only returns positions with per-satellite timestamp < 5 min.
             * 2. Anchor time: for new markers we use position_updated_utc (when that position was computed) so cache age is real; else "when we received the data". For track lead we use fetchedAt.
             * 3. Estimated position every 100 ms (satPassInterpolateTick): track lead line at elapsed time, or anchor + velocity * (now - anchorTime).
             * 4. Dot and label at estimated position. New markers are placed at estimated position (cached + velocity * age) from first paint. On locations fetch we re-anchor at current estimated position and refresh velocity.
             */
            var satPassDefaultColorPalette = [
                '#e6194b', '#3cb44b', '#4363d8', '#f58231', '#911eb4', '#46f0f0',
                '#f032e6', '#bcf60c', '#fabebe', '#008080', '#e6beff', '#9a6324',
                '#fffac8', '#800000', '#aaffc3', '#808000', '#ffd8b1', '#000075'
            ];
            function satPassColorForNorad(noradId) {
                var idx = Math.abs(parseInt(noradId, 10) || 0) % satPassDefaultColorPalette.length;
                return satPassDefaultColorPalette[idx];
            }
            function satPassColorFromSettings(satEntry, noradId) {
                var hex = (satEntry && satEntry.color && typeof satEntry.color === 'string') ? String(satEntry.color).trim() : '';
                if (hex && /^#[0-9A-Fa-f]{3}([0-9A-Fa-f]{3}([0-9A-Fa-f]{2})?)?$/.test(hex)) return hex;
                return satPassColorForNorad(noradId);
            }
            function hasMapOverlayModule(moduleId) {
                return Array.isArray(window.GLANCERF_MAP_OVERLAY_MODULES) && window.GLANCERF_MAP_OVERLAY_MODULES.indexOf(moduleId) >= 0;
            }
            function hasMapOverlayForModule(moduleId) {
                return document.querySelectorAll('.grid-cell-' + moduleId).length > 0 || hasMapOverlayModule(moduleId);
            }
            function getModuleSettings(moduleId) {
                var instances = getAllModuleSettingsInstances(moduleId);
                return instances.length > 0 ? instances[0] : {};
            }
            function mergeObjectsWithOrBooleans(acc, obj) {
                if (!obj || typeof obj !== 'object' || Array.isArray(obj)) return acc || {};
                var out = {};
                if (acc) for (var kk in acc) { if (Object.prototype.hasOwnProperty.call(acc, kk)) out[kk] = acc[kk]; }
                for (var k in obj) {
                    if (!Object.prototype.hasOwnProperty.call(obj, k)) continue;
                    var v = obj[k];
                    var existing = out[k];
                    if (v && typeof v === 'object' && !Array.isArray(v)) {
                        out[k] = mergeObjectsWithOrBooleans(existing, v);
                    } else if (typeof v === 'boolean' || v === true || v === false || v === 'true' || v === 'false') {
                        out[k] = !!(existing || v === true || v === 'true');
                    } else if (v !== undefined && v !== null && String(v).trim() !== '') {
                        if (!existing || existing === '' || existing === null) out[k] = v;
                    }
                }
                return out;
            }
            function getMergedModuleSettings(moduleId) {
                var instances = getAllModuleSettingsInstances(moduleId);
                var schema = (window.GLANCERF_MODULES_SETTINGS_SCHEMA || {})[moduleId] || [];
                var schemaById = {};
                for (var i = 0; i < schema.length; i++) {
                    if (schema[i] && schema[i].id) schemaById[schema[i].id] = schema[i];
                }
                var merged = {};
                for (var s = 0; s < instances.length; s++) {
                    var inst = instances[s];
                    for (var key in inst) {
                        if (!Object.prototype.hasOwnProperty.call(inst, key)) continue;
                        var val = inst[key];
                        var schemaEntry = schemaById[key];
                        var stype = (schemaEntry && schemaEntry.type) || '';
                        if (stype === 'checkbox') {
                            merged[key] = !!(merged[key] || val === true || val === 'true' || val === 1 || val === '1');
                        } else if (typeof val === 'string' && val.trim() && (val.trim().charAt(0) === '{' || val.trim().charAt(0) === '[')) {
                            try {
                                var parsed = JSON.parse(val);
                                if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
                                    merged[key] = mergeObjectsWithOrBooleans(merged[key], parsed);
                                } else if (merged[key] === undefined) {
                                    merged[key] = val;
                                }
                            } catch (e) {
                                if (merged[key] === undefined) merged[key] = val;
                            }
                        } else {
                            if (merged[key] === undefined || merged[key] === '' || merged[key] === null) {
                                if (val !== undefined && val !== null && String(val).trim() !== '') merged[key] = val;
                            }
                        }
                    }
                }
                return merged;
            }
            function getAllModuleSettingsInstances(moduleId) {
                var out = [];
                var all = window.GLANCERF_MODULE_SETTINGS || {};
                var layout = Array.isArray(window.GLANCERF_MAP_OVERLAY_LAYOUT) ? window.GLANCERF_MAP_OVERLAY_LAYOUT : [];
                for (var j = 0; j < layout.length; j++) {
                    if (layout[j] === moduleId) {
                        var ms = all['map_overlay_' + j];
                        if (ms && typeof ms === 'object') out.push(ms);
                    }
                }
                var cells = document.querySelectorAll('.grid-cell-' + moduleId);
                for (var i = 0; i < cells.length; i++) {
                    var r = cells[i].getAttribute('data-row');
                    var c = cells[i].getAttribute('data-col');
                    var key = (r != null && c != null) ? r + '_' + c : '';
                    if (key) {
                        var ms = all[key];
                        if (ms && typeof ms === 'object') out.push(ms);
                    }
                }
                return out;
            }
            function hasSatellitePassOverlay() {
                return hasMapOverlayForModule('satellite_pass');
            }
            function getSatellitePassSettings() {
                var merged = getMergedModuleSettings('satellite_pass');
                var sat = merged.sat_satellites;
                if (sat && typeof sat === 'object') return sat;
                return {};
            }
            var TRACKS_STEP_SEC = 120;
            function satPassInterpolateTick() {
                var now = Date.now();
                document.querySelectorAll('.grid-cell-map .map_container').forEach(function(el) {
                    var map = el._map;
                    if (!map || !map._satellitePassMarkers) return;
                    var markers = map._satellitePassMarkers;
                    var labelMarkers = map._satellitePassLabelMarkers || {};
                    var trackLead = map._satellitePassTrackLead || {};
                    Object.keys(markers).forEach(function(noradStr) {
                        var m = markers[noradStr];
                        var norad = parseInt(noradStr, 10);
                        var leadData = trackLead[noradStr];
                        var lat, lon;
                        if (leadData && leadData.lead && leadData.lead.length > 0 && leadData.fetchedAt != null) {
                            var elapsedSec = (now - leadData.fetchedAt) / 1000;
                            var idx = Math.floor(elapsedSec / TRACKS_STEP_SEC);
                            var lead = leadData.lead;
                            if (idx >= lead.length - 1) {
                                var last = lead[lead.length - 1];
                                lat = last[0];
                                lon = last[1];
                            } else if (idx < 0) {
                                lat = lead[0][0];
                                lon = lead[0][1];
                            } else {
                                var frac = (elapsedSec / TRACKS_STEP_SEC) - idx;
                                var a = lead[idx];
                                var b = lead[idx + 1];
                                lat = a[0] + frac * (b[0] - a[0]);
                                lon = a[1] + frac * (b[1] - a[1]);
                                while (lon > 180) lon -= 360;
                                while (lon < -180) lon += 360;
                            }
                            m.setLatLng([lat, lon]);
                            if (labelMarkers[noradStr]) labelMarkers[noradStr].setLatLng([lat, lon]);
                            return;
                        }
                        if (m._anchorTime == null) return;
                        var dtSec = (now - m._anchorTime) / 1000;
                        lat = m._anchorLat + (m._vlat || 0) * dtSec;
                        lon = m._anchorLon + (m._vlon || 0) * dtSec;
                        while (lon > 180) lon -= 360;
                        while (lon < -180) lon += 360;
                        if (lat > 90) lat = 90;
                        if (lat < -90) lat = -90;
                        m.setLatLng([lat, lon]);
                        if (labelMarkers[noradStr]) labelMarkers[noradStr].setLatLng([lat, lon]);
                    });
                });
            }
            function addSatellitePassLocationsOverlay(map) {
                if (typeof L === 'undefined') return;
                if (!hasSatellitePassOverlay()) {
                    /* Hide overlay only; keep layer and markers so we do not recreate all dots at cached position when panel reappears. */
                    if (map._satellitePassLocationsLayerGroup && map.hasLayer(map._satellitePassLocationsLayerGroup)) {
                        map.removeLayer(map._satellitePassLocationsLayerGroup);
                    }
                    return;
                }
                var layerGroup = map._satellitePassLocationsLayerGroup;
                if (!layerGroup) {
                    layerGroup = L.layerGroup();
                    map._satellitePassLocationsLayerGroup = layerGroup;
                    map._satellitePassMarkers = {};
                    map._satellitePassLabelMarkers = {};
                    layerGroup.addTo(map);
                } else if (!map.hasLayer(layerGroup)) {
                    layerGroup.addTo(map);
                }
                var base = getMapApiBase();
                var locationsUrl = base + '/api/satellite/locations';
                var listUrl = base + '/api/satellite/list';
                Promise.all([
                    fetch(locationsUrl).then(function(r) { return r.ok ? r.json() : { positions: {}, velocities: {}, position_updated_utc: {} }; }),
                    fetch(listUrl).then(function(r) { return r.ok ? r.json() : { satellites: [] }; })
                ]).then(function(results) {
                    var data = results[0];
                    var listData = results[1];
                    var positions = (data && data.positions) ? data.positions : {};
                    var velocities = (data && data.velocities) ? data.velocities : {};
                    var positionUpdatedUtc = (data && data.position_updated_utc) ? data.position_updated_utc : {};
                    var satellites = (listData && listData.satellites) ? listData.satellites : [];
                    var namesByNorad = {};
                    satellites.forEach(function(s) {
                        var n = s.norad_id != null ? parseInt(s.norad_id, 10) : NaN;
                        if (!isNaN(n) && s.name) namesByNorad[String(n)] = String(s.name).trim();
                    });
                    var noradIds = Object.keys(positions).map(function(k) { return parseInt(k, 10); }).filter(function(n) { return !isNaN(n); });
                    if (noradIds.length === 0) return;
                    var satSettings = getSatellitePassSettings();
                    noradIds = noradIds.filter(function(norad) {
                        var e = satSettings[String(norad)];
                        return (e && e.show_on_map === false) ? false : true;
                    });
                    var markers = map._satellitePassMarkers || {};
                    var labelMarkers = map._satellitePassLabelMarkers || {};
                    map._satellitePassLabelMarkers = labelMarkers;
                    var now = Date.now();
                    function positionTimeMs(noradKey) {
                        var s = positionUpdatedUtc[noradKey];
                        if (typeof s !== 'string' || !s) return null;
                        var ms = Date.parse(s);
                        return isNaN(ms) ? null : ms;
                    }
                    noradIds.forEach(function(norad) {
                        var noradKey = String(norad);
                        var ll = positions[noradKey];
                        if (!Array.isArray(ll) || ll.length < 2) return;
                        var lat = Number(ll[0]);
                        var lon = Number(ll[1]);
                        if (isNaN(lat) || isNaN(lon)) return;
                        var vel = velocities[noradKey];
                        var vlat = 0, vlon = 0;
                        if (Array.isArray(vel) && vel.length >= 2) {
                            vlat = Number(vel[0]) || 0;
                            vlon = Number(vel[1]) || 0;
                        }
                        var m = markers[norad];
                        if (m) {
                            /* Advance anchor to current estimated position (interpolation owns position). Update velocity from API so future interpolation stays accurate; never set position to cached lat/lon. */
                            var current = m.getLatLng();
                            if (current) {
                                m._anchorLat = current.lat;
                                m._anchorLon = current.lng;
                                m._anchorTime = now;
                                m._vlat = vlat;
                                m._vlon = vlon;
                            }
                            var satEntry = satSettings[noradKey];
                            var color = satPassColorFromSettings(satEntry, norad);
                            m.setStyle({ fillColor: color });
                        } else {
                            var anchorTimeMs = positionTimeMs(noradKey) || now;
                            var dtSec = (now - anchorTimeMs) / 1000;
                            var estLat = lat + (vlat * dtSec);
                            var estLon = lon + (vlon * dtSec);
                            while (estLon > 180) estLon -= 360;
                            while (estLon < -180) estLon += 360;
                            if (estLat > 90) estLat = 90;
                            if (estLat < -90) estLat = -90;
                            var satEntry = satSettings[noradKey];
                            var color = satPassColorFromSettings(satEntry, norad);
                            m = L.circleMarker([estLat, estLon], {
                                radius: 5, /* match .grid-cell-map --sat-pass-dot-radius if changed */
                                fillColor: color,
                                color: '#fff',
                                weight: 1,
                                fillOpacity: 0.9
                            });
                            m._anchorLat = lat;
                            m._anchorLon = lon;
                            m._anchorTime = anchorTimeMs;
                            m._vlat = vlat;
                            m._vlon = vlon;
                            m.addTo(layerGroup);
                            markers[norad] = m;
                            if (satEntry.show_label !== false) {
                                var name = (namesByNorad[noradKey] || 'NORAD ' + norad).substring(0, 24);
                                var labelHtml = '<div class="sat-pass-label-wrap"><svg class="sat-pass-label-line" viewBox="0 0 24 8" preserveAspectRatio="none"><line x1="0" y1="0" x2="24" y2="8" stroke="#333" vector-effect="non-scaling-stroke"/></svg><div class="sat-pass-label-bubble-wrap"><div class="sat-pass-label"><span class="sat-pass-label-name">' + escapeHtml(name) + '</span><span class="sat-pass-label-norad">' + norad + '</span></div></div></div>';
                                var labelIcon = L.divIcon({
                                    html: labelHtml,
                                    className: 'sat-pass-label-icon',
                                    iconSize: null,
                                    iconAnchor: [0, 0]
                                });
                                var labelM = L.marker([estLat, estLon], { icon: labelIcon });
                                labelM._norad = norad;
                                labelM.addTo(layerGroup);
                                labelMarkers[norad] = labelM;
                            }
                            scheduleTraceRetryForNorad(map, norad);
                        }
                    });
                    Object.keys(markers).forEach(function(noradStr) {
                        var norad = parseInt(noradStr, 10);
                        var remove = positions[String(norad)] == null;
                        if (!remove) {
                            var e = satSettings[noradStr];
                            if (e && e.show_on_map === false) remove = true;
                        }
                        if (remove) {
                            layerGroup.removeLayer(markers[norad]);
                            delete markers[norad];
                            if (labelMarkers[norad]) {
                                layerGroup.removeLayer(labelMarkers[norad]);
                                delete labelMarkers[norad];
                            }
                            if (map._satellitePassTracePendingNorads) delete map._satellitePassTracePendingNorads[norad];
                        } else {
                            var e = satSettings[noradStr];
                            if (e && e.show_label === false && labelMarkers[norad]) {
                                layerGroup.removeLayer(labelMarkers[norad]);
                                delete labelMarkers[norad];
                            } else if ((!e || e.show_label !== false) && markers[norad] && !labelMarkers[norad]) {
                                var pos = markers[norad].getLatLng();
                                var name = (namesByNorad[noradStr] || 'NORAD ' + norad).substring(0, 24);
                                var labelHtml = '<div class="sat-pass-label-wrap"><svg class="sat-pass-label-line" viewBox="0 0 24 8" preserveAspectRatio="none"><line x1="0" y1="0" x2="24" y2="8" stroke="#333" vector-effect="non-scaling-stroke"/></svg><div class="sat-pass-label-bubble-wrap"><div class="sat-pass-label"><span class="sat-pass-label-name">' + escapeHtml(name) + '</span><span class="sat-pass-label-norad">' + norad + '</span></div></div></div>';
                                var labelIcon = L.divIcon({
                                    html: labelHtml,
                                    className: 'sat-pass-label-icon',
                                    iconSize: null,
                                    iconAnchor: [0, 0]
                                });
                                var labelM = L.marker([pos.lat, pos.lng], { icon: labelIcon });
                                labelM._norad = norad;
                                labelM.addTo(layerGroup);
                                labelMarkers[norad] = labelM;
                            }
                        }
                    });
                    if (!map.hasLayer(layerGroup)) layerGroup.addTo(map);
                    layerGroup.bringToFront();
                    redrawSatellitePassTracksFromCache(map);
                }).catch(function() {});
            }
            function escapeHtml(s) {
                if (!s) return '';
                var div = document.createElement('div');
                div.textContent = s;
                return div.innerHTML;
            }
            function splitPathAtWrapBoundaries(path) {
                if (!path || path.length < 2) return path.length >= 2 ? [path] : [];
                var segments = [];
                var seg = [path[0]];
                for (var i = 1; i < path.length; i++) {
                    var a = path[i - 1];
                    var b = path[i];
                    var lat1 = a[0], lon1 = a[1], lat2 = b[0], lon2 = b[1];
                    var dlon = Math.abs(lon2 - lon1);
                    var crossesAntimeridian = dlon > 180;
                    var nearPole = Math.min(Math.abs(lat1), Math.abs(lat2)) > 80;
                    var largeLonJumpNearPole = nearPole && dlon > 90;
                    var crossesPole = Math.abs(lat2 - lat1) > 90;
                    if (crossesAntimeridian || largeLonJumpNearPole || crossesPole) {
                        if (seg.length >= 2) segments.push(seg);
                        seg = [b];
                    } else {
                        seg.push(b);
                    }
                }
                if (seg.length >= 2) segments.push(seg);
                return segments;
            }
            var SAT_TRACE_RETRY_INTERVAL_MS = 15000;
            var SAT_TRACE_RETRY_MAX = 8;
            function scheduleTraceRetryForNorad(map, norad) {
                if (!map || norad == null) return;
                if (!hasSatellitePassOverlay()) {
                    if (map._satellitePassTracePendingNorads) delete map._satellitePassTracePendingNorads[norad];
                    return;
                }
                var pending = map._satellitePassTracePendingNorads;
                if (!pending) {
                    pending = {};
                    map._satellitePassTracePendingNorads = pending;
                }
                if (pending[norad] == null) pending[norad] = 0;
                var base = getMapApiBase();
                var tracksUrl = base + '/api/satellite/tracks';
                fetch(tracksUrl).then(function(r) {
                    if (!r.ok) return { tracks: {} };
                    return r.json();
                }).then(function(data) {
                    if (!hasSatellitePassOverlay()) return;
                    var tracks = (data && data.tracks) ? data.tracks : {};
                    if (tracks[String(norad)]) {
                        delete pending[norad];
                        addSatellitePassTracksOverlay(map);
                    } else {
                        pending[norad] = (pending[norad] || 0) + 1;
                        if (pending[norad] < SAT_TRACE_RETRY_MAX) {
                            setTimeout(function() { scheduleTraceRetryForNorad(map, norad); }, SAT_TRACE_RETRY_INTERVAL_MS);
                        } else {
                            delete pending[norad];
                        }
                    }
                }).catch(function() {
                    pending[norad] = (pending[norad] || 0) + 1;
                    if (pending[norad] < SAT_TRACE_RETRY_MAX) {
                        setTimeout(function() { scheduleTraceRetryForNorad(map, norad); }, SAT_TRACE_RETRY_INTERVAL_MS);
                    } else {
                        delete pending[norad];
                    }
                });
            }
            function drawSatellitePassTracksFromData(map, tracks, fetchedAt) {
                var layerGroup = map._satellitePassTracksLayerGroup;
                if (!layerGroup) return;
                if (!map._satellitePassTrackLead) map._satellitePassTrackLead = {};
                var satSettings = getSatellitePassSettings();
                var markers = map._satellitePassMarkers || {};
                layerGroup.clearLayers();
                Object.keys(tracks).forEach(function(noradStr) {
                    var norad = parseInt(noradStr, 10);
                    if (isNaN(norad)) return;
                    if (satSettings[noradStr] && satSettings[noradStr].show_traces === false) return;
                    var satEntry = satSettings[noradStr];
                    var t = tracks[noradStr];
                    var tail = (t && t.tail) ? t.tail : [];
                    var lead = (t && t.lead) ? t.lead : [];
                    var path = [];
                    tail.forEach(function(p) {
                        if (Array.isArray(p) && p.length >= 2) path.push([Number(p[0]), Number(p[1])]);
                    });
                    var leadPoints = [];
                    lead.forEach(function(p) {
                        if (Array.isArray(p) && p.length >= 2) {
                            path.push([Number(p[0]), Number(p[1])]);
                            leadPoints.push([Number(p[0]), Number(p[1])]);
                        }
                    });
                    if (leadPoints.length > 0) {
                        var useFetchedAt = fetchedAt;
                        var existing = map._satellitePassTrackLead && map._satellitePassTrackLead[noradStr];
                        if (existing && existing.fetchedAt != null) {
                            useFetchedAt = existing.fetchedAt;
                        } else {
                            var m = markers[noradStr];
                            if (m) {
                                var current = m.getLatLng();
                                if (current && leadPoints.length > 0) {
                                    var bestIdx = 0;
                                    var bestDist = 1e9;
                                    for (var i = 0; i < leadPoints.length; i++) {
                                        var d = (leadPoints[i][0] - current.lat) * (leadPoints[i][0] - current.lat) + (leadPoints[i][1] - current.lng) * (leadPoints[i][1] - current.lng);
                                        if (d < bestDist) { bestDist = d; bestIdx = i; }
                                    }
                                    useFetchedAt = fetchedAt - bestIdx * TRACKS_STEP_SEC * 1000;
                                }
                            }
                        }
                        map._satellitePassTrackLead[noradStr] = { lead: leadPoints, fetchedAt: useFetchedAt };
                    }
                    var segments = splitPathAtWrapBoundaries(path);
                    var color = satPassColorFromSettings(satEntry, norad);
                    function addPolylineForSegment(seg, lonOffset) {
                        var pts = seg.map(function(p) { return [p[0], p[1] + lonOffset]; });
                        L.polyline(pts, {
                            color: color,
                            weight: 2,
                            opacity: 0.65,
                            smoothFactor: 1
                        }).addTo(layerGroup);
                    }
                    segments.forEach(function(seg) {
                        addPolylineForSegment(seg, 0);
                        addPolylineForSegment(seg, 360);
                        addPolylineForSegment(seg, -360);
                    });
                });
                Object.keys(map._satellitePassTrackLead || {}).forEach(function(noradStr) {
                    if (satSettings[noradStr] && satSettings[noradStr].show_traces === false) {
                        delete map._satellitePassTrackLead[noradStr];
                    }
                });
                if (!map.hasLayer(layerGroup)) layerGroup.addTo(map);
                layerGroup.bringToBack();
                if (map._satellitePassLocationsLayerGroup && map.hasLayer(map._satellitePassLocationsLayerGroup)) {
                    map._satellitePassLocationsLayerGroup.bringToFront();
                }
            }
            function addSatellitePassTracksOverlay(map) {
                if (typeof L === 'undefined') return;
                if (!hasSatellitePassOverlay()) {
                    if (map._satellitePassTracksLayerGroup) {
                        map.removeLayer(map._satellitePassTracksLayerGroup);
                        map._satellitePassTracksLayerGroup = null;
                    }
                    map._satellitePassTrackLead = {};
                    map._satellitePassTracksCache = null;
                    return;
                }
                var layerGroup = map._satellitePassTracksLayerGroup;
                if (!layerGroup) {
                    layerGroup = L.layerGroup();
                    map._satellitePassTracksLayerGroup = layerGroup;
                    map._satellitePassTrackLead = {};
                    layerGroup.addTo(map);
                }
                var base = getMapApiBase();
                var tracksUrl = base + '/api/satellite/tracks';
                fetch(tracksUrl).then(function(r) {
                    if (!r.ok) return { tracks: {} };
                    return r.json();
                }).then(function(data) {
                    var tracks = (data && data.tracks) ? data.tracks : {};
                    var fetchedAt = Date.now();
                    map._satellitePassTracksCache = { tracks: tracks, fetchedAt: fetchedAt };
                    if (!map._satellitePassTrackLead) map._satellitePassTrackLead = {};
                    var trackCount = Object.keys(tracks).length;
                    if (trackCount === 0) {
                        var retries = (map._satellitePassTracksRetryCount != null) ? map._satellitePassTracksRetryCount : 0;
                        map._satellitePassTracksRetryCount = retries + 1;
                        if (retries < 3 && hasSatellitePassOverlay()) {
                            setTimeout(function() { addSatellitePassTracksOverlay(map); }, 20000);
                        }
                    } else {
                        map._satellitePassTracksRetryCount = 0;
                    }
                    drawSatellitePassTracksFromData(map, tracks, fetchedAt);
                }).catch(function() {});
            }
            function redrawSatellitePassTracksFromCache(map) {
                var cache = map._satellitePassTracksCache;
                if (!cache || !cache.tracks) return;
                drawSatellitePassTracksFromData(map, cache.tracks, cache.fetchedAt);
            }
            function applyOverlays(map, cfg) {
                if (cfg.grid_style && cfg.grid_style !== 'none') addGridOverlay(map, cfg.grid_style);
                if (cfg.show_terminator) addTerminatorOverlay(map);
                if (cfg.show_sun_moon) addSunMoonOverlay(map);
                if (cfg.show_aurora) addAuroraOverlay(map, cfg);
                if (cfg.propagation_source && cfg.propagation_source !== 'none') addPropagationOverlay(map, cfg);
                if (hasMapOverlayForModule('aprs')) addAprsLocationsOverlay(map, cfg);
                if (hasMapOverlayForModule('live_spots')) addLiveSpotsLinesOverlay(map);
                addQthMarkerOverlay(map);
                addSatNewLocationsOverlay(map);
                addSatellitePassLocationsOverlay(map);
                addSatellitePassTracksOverlay(map);
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
                /* Refresh overlays only for map containers (map module must be in layout to get here). */
                if (!window._glancerfPropagationRefreshStarted) {
                    window._glancerfPropagationRefreshStarted = true;
                    setInterval(function() {
                        document.querySelectorAll('.grid-cell-map .map_container').forEach(function(el) {
                            if (!el._map) return;
                            var cfg = getMapSettings(el);
                            if (cfg.show_aurora) addAuroraOverlay(el._map, cfg);
                            if (cfg.propagation_source && cfg.propagation_source !== 'none') addPropagationOverlay(el._map, cfg);
                            if (hasMapOverlayForModule('aprs')) addAprsLocationsOverlay(el._map, cfg);
                            if (hasMapOverlayForModule('live_spots')) addLiveSpotsLinesOverlay(el._map);
                            addSatNewLocationsOverlay(el._map);
                            addSatellitePassLocationsOverlay(el._map);
                        });
                    }, PROPAGATION_REFRESH_MS);
                }
                /* APRS overlay: refresh every 10 s when aprs in overlay (live feed). */
                if (!window._glancerfAprsOverlayRefreshStarted) {
                    window._glancerfAprsOverlayRefreshStarted = true;
                    setInterval(function() {
                        if (!hasMapOverlayForModule('aprs')) return;
                        document.querySelectorAll('.grid-cell-map .map_container').forEach(function(el) {
                            if (!el._map) return;
                            var cfg = getMapSettings(el);
                            addAprsLocationsOverlay(el._map, cfg);
                        });
                    }, 10000);
                    document.addEventListener('glancerf_aprs_update', function() {
                        if (!hasMapOverlayForModule('aprs')) return;
                        document.querySelectorAll('.grid-cell-map .map_container').forEach(function(el) {
                            if (!el._map) return;
                            var cfg = getMapSettings(el);
                            addAprsLocationsOverlay(el._map, cfg);
                        });
                    });
                }
                /* Satellite positions: refresh from cache every 5 s so new dots appear as soon as each position is written. */
                if (!window._glancerfSatelliteLocationsRefreshStarted) {
                    window._glancerfSatelliteLocationsRefreshStarted = true;
                    setInterval(function() {
                        if (!hasSatellitePassOverlay()) return;
                        document.querySelectorAll('.grid-cell-map .map_container').forEach(function(el) {
                            if (!el._map) return;
                            addSatellitePassLocationsOverlay(el._map);
                        });
                    }, 5000);
                }
                /* Interpolate satellite dot positions between API pings using velocity (deg/s). */
                if (!window._glancerfSatelliteInterpolationStarted) {
                    window._glancerfSatelliteInterpolationStarted = true;
                    setInterval(satPassInterpolateTick, 100);
                }
                /* Satellite tracks (tail + lead): refresh from cache every 5 min. */
                if (!window._glancerfSatelliteTracksRefreshStarted) {
                    window._glancerfSatelliteTracksRefreshStarted = true;
                    setInterval(function() {
                        if (!hasSatellitePassOverlay()) return;
                        document.querySelectorAll('.grid-cell-map .map_container').forEach(function(el) {
                            if (!el._map) return;
                            addSatellitePassTracksOverlay(el._map);
                        });
                    }, 5 * 60 * 1000);
                }
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