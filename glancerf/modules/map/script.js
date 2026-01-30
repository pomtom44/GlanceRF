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
                return { zoom: zoom, lat: lat, lng: lng, map_style: mapStyle, tile_style: tileStyle };
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
                    }).setView([cfg.lat, cfg.lng], zoom);
                    getTileConfig(cfg.map_style, cfg.tile_style).addTo(el._map);
                    el._map.invalidateSize();
                    if (typeof ResizeObserver !== 'undefined') {
                        el._resizeObserver = new ResizeObserver(function() {
                            if (el._map && el._map.invalidateSize) el._map.invalidateSize();
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