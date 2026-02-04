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
                var showAprsLocations = (ms.show_aprs_locations === '1' || ms.show_aprs_locations === true);
                var aprsDisplayMode = (ms.aprs_display_mode === 'icons') ? 'icons' : 'dots';
                var aprsFilter = (ms.aprs_filter != null && typeof ms.aprs_filter === 'string') ? ms.aprs_filter.trim() : '';
                return { zoom: zoom, lat: lat, lng: lng, map_style: mapStyle, tile_style: tileStyle, grid_style: gridStyle, show_terminator: showTerminator, show_sun_moon: showSunMoon, show_aurora: showAurora, aurora_opacity: auroraOpacity, propagation_source: propagationSource, propagation_opacity: propagationOpacity, propagation_aprs_hours: propagationAprsHours, show_aprs_locations: showAprsLocations, aprs_display_mode: aprsDisplayMode, aprs_filter: aprsFilter };
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
                else if (sourceId === 'tropo') { valMin = 250; valMax = 400; }
                else if (sourceId === 'vhf_aprs') { valMin = 20; valMax = 600; }
                else { valMin = 0; valMax = 1; }
                var url = '/api/map/propagation-data?source=' + encodeURIComponent(sourceId);
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
                    if (sourceId === 'vhf_aprs' && coords && coords.length >= 3) {
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
                    if (!coords || coords.length < 3) {
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
                    L.imageOverlay(url, bounds, { opacity: 1 }).addTo(layerGroup);
                    L.imageOverlay(url, [[-90, 180], [90, 540]], { opacity: 1 }).addTo(layerGroup);
                    L.imageOverlay(url, [[-90, -540], [90, -180]], { opacity: 1 }).addTo(layerGroup);
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
            function getAprsSymbolDivIcon(symbolTable, symbol) {
                var tableIdx = (symbolTable === '\\') ? 1 : 0;
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
                return L.divIcon({
                    html: html,
                    className: 'aprs-symbol-icon-wrap',
                    iconSize: [cell, cell],
                    iconAnchor: [0, cell / 2]
                });
            }
            function applyAprsLocationsFilter(locs, filterStr) {
                if (!filterStr || !locs || !locs.length) return locs;
                var prefixes = [];
                var parts = filterStr.split(/\s+/);
                for (var i = 0; i < parts.length; i++) {
                    var p = parts[i];
                    if (p.indexOf('p/') === 0) {
                        var rest = p.slice(2).split('/');
                        for (var j = 0; j < rest.length; j++) {
                            if (rest[j]) prefixes.push(rest[j].toUpperCase());
                        }
                    }
                }
                if (prefixes.length === 0) return locs;
                return locs.filter(function(loc) {
                    var call = (loc.callsign || '').toUpperCase().split('-')[0];
                    for (var k = 0; k < prefixes.length; k++) {
                        if (call.indexOf(prefixes[k]) === 0) return true;
                    }
                    return false;
                });
            }
            function addAprsLocationsOverlay(map, cfg) {
                var layerGroup = map._aprsLocationsLayerGroup;
                if (!layerGroup) {
                    layerGroup = L.layerGroup();
                    map._aprsLocationsLayerGroup = layerGroup;
                    layerGroup.addTo(map);
                }
                layerGroup.clearLayers();
                var hours = (cfg && cfg.propagation_aprs_hours) ? cfg.propagation_aprs_hours : 6;
                var ageLimitHours = typeof hours === 'number' ? hours : parseFloat(hours, 10) || 6;
                var displayMode = (cfg && cfg.aprs_display_mode === 'icons') ? 'icons' : 'dots';
                var url = '/api/map/aprs-locations?hours=' + encodeURIComponent(hours);
                fetch(url).then(function(r) {
                    if (!r.ok) return { locations: [] };
                    return r.json();
                }).then(function(data) {
                    var locs = data && data.locations;
                    if (!locs || !locs.length) return;
                    locs = applyAprsLocationsFilter(locs, cfg && cfg.aprs_filter ? cfg.aprs_filter : '');
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
            function applyOverlays(map, cfg) {
                if (cfg.grid_style && cfg.grid_style !== 'none') addGridOverlay(map, cfg.grid_style);
                if (cfg.show_terminator) addTerminatorOverlay(map);
                if (cfg.show_sun_moon) addSunMoonOverlay(map);
                if (cfg.show_aurora) addAuroraOverlay(map, cfg);
                if (cfg.propagation_source && cfg.propagation_source !== 'none') addPropagationOverlay(map, cfg);
                if (cfg.show_aprs_locations) addAprsLocationsOverlay(map, cfg);
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
                if (!window._glancerfPropagationRefreshStarted) {
                    window._glancerfPropagationRefreshStarted = true;
                    setInterval(function() {
                        document.querySelectorAll('.grid-cell-map .map_container').forEach(function(el) {
                            if (!el._map) return;
                            var cfg = getMapSettings(el);
                            if (cfg.propagation_source && cfg.propagation_source !== 'none') addPropagationOverlay(el._map, cfg);
                            if (cfg.show_aprs_locations) addAprsLocationsOverlay(el._map, cfg);
                        });
                    }, PROPAGATION_REFRESH_MS);
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