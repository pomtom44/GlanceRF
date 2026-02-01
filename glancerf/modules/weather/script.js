(function() {
            var WEATHER_UPDATE_MS = 15 * 60 * 1000;
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
            var WMO_CODES = {
                0: "Clear", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
                45: "Foggy", 48: "Rime fog", 51: "Light drizzle", 53: "Drizzle", 55: "Dense drizzle",
                56: "Freezing drizzle", 57: "Dense freezing drizzle", 61: "Slight rain", 63: "Rain", 65: "Heavy rain",
                66: "Freezing rain", 67: "Heavy freezing rain", 71: "Slight snow", 73: "Snow", 75: "Heavy snow",
                77: "Snow grains", 80: "Slight showers", 81: "Showers", 82: "Violent showers",
                85: "Slight snow showers", 86: "Heavy snow showers", 95: "Thunderstorm",
                96: "Thunderstorm, hail", 99: "Thunderstorm, heavy hail"
            };
            function weatherCodeToText(code) {
                if (code == null || code === undefined) return "";
                return WMO_CODES[code] || "Unknown";
            }
            function showElements(cell, data, ms) {
                var placeEl = cell.querySelector('.weather_place');
                var condEl = cell.querySelector('.weather_conditions');
                var tempEl = cell.querySelector('.weather_temp');
                var feelsEl = cell.querySelector('.weather_feels');
                var humEl = cell.querySelector('.weather_humidity');
                var windEl = cell.querySelector('.weather_wind');
                var pressEl = cell.querySelector('.weather_pressure');
                var errEl = cell.querySelector('.weather_error');
                var loadEl = cell.querySelector('.weather_loading');
                if (errEl) { errEl.style.display = 'none'; errEl.textContent = ''; }
                if (loadEl) loadEl.style.display = 'none';
                if (data && data.current) {
                    var c = data.current;
                    if (placeEl) { placeEl.textContent = data.locationLabel || ''; placeEl.style.display = data.locationLabel ? '' : 'none'; }
                    if (condEl && isOn(ms.show_conditions)) {
                        condEl.textContent = weatherCodeToText(c.weather_code);
                        condEl.style.display = c.weather_code != null ? '' : 'none';
                    } else if (condEl) condEl.style.display = 'none';
                    if (tempEl && isOn(ms.show_temperature)) {
                        tempEl.textContent = (c.temperature_2m != null) ? (Math.round(c.temperature_2m) + ' ' + (data.temp_unit || 'C')) : '';
                        tempEl.style.display = tempEl.textContent ? '' : 'none';
                    } else if (tempEl) tempEl.style.display = 'none';
                    if (feelsEl && isOn(ms.show_feels_like)) {
                        feelsEl.textContent = (c.apparent_temperature != null) ? ('Feels like ' + Math.round(c.apparent_temperature) + ' ' + (data.temp_unit || 'C')) : '';
                        feelsEl.style.display = feelsEl.textContent ? '' : 'none';
                    } else if (feelsEl) feelsEl.style.display = 'none';
                    if (humEl && isOn(ms.show_humidity)) {
                        humEl.textContent = (c.relative_humidity_2m != null) ? ('Humidity ' + c.relative_humidity_2m + '%') : '';
                        humEl.style.display = humEl.textContent ? '' : 'none';
                    } else if (humEl) humEl.style.display = 'none';
                    if (windEl && isOn(ms.show_wind)) {
                        var w = [];
                        if (c.wind_speed_10m != null) w.push(c.wind_speed_10m + ' ' + (data.wind_unit || 'km/h'));
                        if (c.wind_direction_10m != null) w.push(c.wind_direction_10m + ' deg');
                        windEl.textContent = w.length ? ('Wind ' + w.join(', ')) : '';
                        windEl.style.display = windEl.textContent ? '' : 'none';
                    } else if (windEl) windEl.style.display = 'none';
                    if (pressEl && isOn(ms.show_pressure)) {
                        var pressStr = '';
                        if (c.surface_pressure != null) {
                            if (data.pressure_unit === 'inHg') {
                                pressStr = 'Pressure ' + (c.surface_pressure / 33.8639).toFixed(2) + ' inHg';
                            } else {
                                pressStr = 'Pressure ' + Math.round(c.surface_pressure) + ' hPa';
                            }
                        }
                        pressEl.textContent = pressStr;
                        pressEl.style.display = pressStr ? '' : 'none';
                    } else if (pressEl) pressEl.style.display = 'none';
                } else {
                    if (placeEl) placeEl.style.display = 'none';
                    if (condEl) condEl.style.display = 'none';
                    if (tempEl) tempEl.style.display = 'none';
                    if (feelsEl) feelsEl.style.display = 'none';
                    if (humEl) humEl.style.display = 'none';
                    if (windEl) windEl.style.display = 'none';
                    if (pressEl) pressEl.style.display = 'none';
                }
            }
            function showError(cell, msg) {
                var errEl = cell.querySelector('.weather_error');
                var loadEl = cell.querySelector('.weather_loading');
                if (loadEl) loadEl.style.display = 'none';
                if (errEl) { errEl.textContent = msg || 'Error'; errEl.style.display = ''; }
            }
            function showLoading(cell, on) {
                var loadEl = cell.querySelector('.weather_loading');
                var errEl = cell.querySelector('.weather_error');
                if (on) {
                    if (errEl) errEl.style.display = 'none';
                    if (loadEl) { loadEl.textContent = 'Loading...'; loadEl.style.display = ''; }
                } else if (loadEl) loadEl.style.display = 'none';
            }
            function getCoord(ms, cb) {
                var locStr = (ms.location || window.GLANCERF_SETUP_LOCATION || '').toString().trim();
                var loc = parseLocation(locStr);
                if (!loc) {
                    cb(null, 'Set grid or lat,lng');
                    return;
                }
                cb(loc);
            }
            function fetchWeather(cell, cellKey, ms, coord, cb) {
                showLoading(cell, true);
                var imperial = (ms.units || 'metric').toLowerCase() === 'imperial';
                var url = 'https://api.open-meteo.com/v1/forecast?latitude=' + encodeURIComponent(coord.lat) + '&longitude=' + encodeURIComponent(coord.lng) +
                    '&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m,wind_direction_10m,surface_pressure&timezone=auto' +
                    '&temperature_unit=' + (imperial ? 'fahrenheit' : 'celsius') +
                    '&wind_speed_unit=' + (imperial ? 'mph' : 'kmh');
                fetch(url).then(function(r) {
                    return r.json().then(function(data) {
                        return { ok: r.ok, status: r.status, data: data };
                    });
                }).then(function(result) {
                    showLoading(cell, false);
                    var data = result.data;
                    if (result.ok && data && data.current) {
                        data.temp_unit = (data.current_units && data.current_units.temperature_2m) || (imperial ? 'F' : 'C');
                        data.wind_unit = (data.current_units && data.current_units.wind_speed_10m) || (imperial ? 'mph' : 'km/h');
                        data.pressure_unit = imperial ? 'inHg' : 'hPa';
                        data.locationLabel = '';
                        cb(data);
                    } else {
                        var msg = 'Weather unavailable';
                        if (data && typeof data.reason === 'string') msg = data.reason;
                        else if (data && typeof data.error === 'string') msg = data.error;
                        else if (!result.ok && result.status) msg = 'Weather unavailable (' + result.status + ')';
                        cb(null, msg);
                    }
                }).catch(function(err) {
                    showLoading(cell, false);
                    var msg = (err && err.message) ? err.message : 'Network error';
                    cb(null, msg);
                });
            }
            function updateCell(cell, cellKey, ms) {
                getCoord(ms, function(coord, errMsg) {
                    if (!coord) {
                        showError(cell, errMsg || 'Set grid or lat,lng');
                        return;
                    }
                    fetchWeather(cell, cellKey, ms, coord, function(data, errorMsg) {
                        if (data && data.current) {
                            showElements(cell, data, ms);
                            var cacheKey = 'weather_cache_' + cellKey;
                            try {
                                window[cacheKey] = { data: data, ts: Date.now() };
                            } catch (e) {}
                        } else {
                            showError(cell, errorMsg || 'Weather unavailable');
                        }
                    });
                });
            }
            function maybeUseCache(cell, cellKey, ms) {
                var cacheKey = 'weather_cache_' + cellKey;
                try {
                    var cached = window[cacheKey];
                    if (cached && (Date.now() - cached.ts) < WEATHER_UPDATE_MS) {
                        showLoading(cell, false);
                        showElements(cell, cached.data, ms);
                        return true;
                    }
                } catch (e) {}
                return false;
            }
            function runAll() {
                var allSettings = window.GLANCERF_MODULE_SETTINGS || {};
                document.querySelectorAll('.grid-cell-weather').forEach(function(cell) {
                    var r = cell.getAttribute('data-row');
                    var c = cell.getAttribute('data-col');
                    var cellKey = (r != null && c != null) ? r + '_' + c : '';
                    var ms = (cellKey && allSettings[cellKey]) ? allSettings[cellKey] : {};
                    if (maybeUseCache(cell, cellKey, ms)) return;
                    updateCell(cell, cellKey, ms);
                });
            }
            runAll();
            setInterval(runAll, WEATHER_UPDATE_MS);
        })();