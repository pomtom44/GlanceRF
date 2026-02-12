(function() {
    var activeStreams = {};
    function getCellKey(cell) {
        var r = cell.getAttribute('data-row');
        var c = cell.getAttribute('data-col');
        return (r != null && c != null) ? r + '_' + c : '';
    }
    function getCellSettings(cell) {
        var allSettings = window.GLANCERF_MODULE_SETTINGS || {};
        var key = getCellKey(cell);
        return (key && allSettings[key]) ? allSettings[key] : {};
    }
    function stopStream(cellKey) {
        var s = activeStreams[cellKey];
        if (s && s.getTracks) {
            s.getTracks().forEach(function(t) { t.stop(); });
        }
        activeStreams[cellKey] = null;
    }
    function parseNum(val, defaultVal, minVal, maxVal) {
        var n = parseInt(val, 10);
        if (isNaN(n)) return defaultVal;
        if (minVal != null && n < minVal) return minVal;
        if (maxVal != null && n > maxVal) return maxVal;
        return n;
    }
    function updateCell(cell) {
        var wrap = cell.querySelector('.webcam_wrap');
        var video = cell.querySelector('.webcam_video');
        var img = cell.querySelector('.webcam_img');
        var placeholder = cell.querySelector('.webcam_placeholder');
        if (!wrap || !video) return;
        var cellKey = getCellKey(cell);
        stopStream(cellKey);
        var settings = getCellSettings(cell);
        var sourceType = (settings.source_type || 'local_user').toLowerCase();
        wrap.classList.remove('has-feed');
        video.style.display = 'none';
        video.removeAttribute('src');
        video.srcObject = null;
        if (img) { img.style.display = 'none'; img.removeAttribute('src'); }
        placeholder.style.display = '';
        if (sourceType === 'local_user') {
            var deviceId = (settings.device_id || '').trim();
            var constraints = { video: true, audio: false };
            if (deviceId) constraints.video = { deviceId: { exact: deviceId } };
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                placeholder.textContent = 'Camera not supported in this browser';
                return;
            }
            if (typeof window.isSecureContext !== 'undefined' && !window.isSecureContext) {
                placeholder.innerHTML = 'Camera blocked for privacy when using an IP address. ' +
                    'Use <strong>https://</strong> or open from <strong>localhost</strong> (e.g. <code>http://localhost:' + (window.location.port || '80') + '</code>) on this machine to allow camera access.';
                placeholder.style.whiteSpace = 'normal';
                placeholder.style.textAlign = 'left';
                return;
            }
            navigator.mediaDevices.getUserMedia(constraints).then(function(stream) {
                if (getCellKey(cell) !== cellKey) {
                    stream.getTracks().forEach(function(t) { t.stop(); });
                    return;
                }
                activeStreams[cellKey] = stream;
                video.srcObject = stream;
                video.style.display = '';
                wrap.classList.add('has-feed');
                placeholder.style.display = 'none';
            }).catch(function(err) {
                var msg = 'Camera access denied or unavailable';
                var name = (err && err.name) ? err.name : '';
                if (name === 'NotAllowedError' || name === 'SecurityError' || (err && err.message && err.message.indexOf('secure') !== -1)) {
                    msg = 'Camera blocked by browser. Use https:// or open from localhost (not by IP) to allow camera.';
                }
                placeholder.textContent = msg;
            });
            return;
        }
        if (sourceType === 'local_server') {
            var devIndex = parseNum(settings.device_index, 0, 0, 4);
            var streamUrl = '/api/webcam/stream?device=' + devIndex;
            if (img) {
                placeholder.textContent = 'Loading stream...';
                placeholder.style.display = '';
                img.style.display = 'none';
                img.src = streamUrl;
                img.onerror = function() {
                    wrap.classList.remove('has-feed');
                    placeholder.style.display = '';
                    placeholder.textContent = 'ffmpeg needs to be installed on the server';
                };
                img.onload = function() {
                    img.style.display = '';
                    wrap.classList.add('has-feed');
                    placeholder.style.display = 'none';
                };
            }
            return;
        }
        if (sourceType === 'remote') {
            var url = (settings.remote_url || '').trim();
            if (!url) {
                placeholder.textContent = 'Enter URL in cell settings';
                return;
            }
            var remoteType = (settings.remote_type || 'mjpeg').toLowerCase();
            if (remoteType === 'mjpeg') {
                placeholder.textContent = 'Loading stream...';
                placeholder.style.display = '';
                img.style.display = 'none';
                img.src = url;
                img.onerror = function() {
                    wrap.classList.remove('has-feed');
                    placeholder.style.display = '';
                    placeholder.textContent = 'Failed to load stream';
                };
                img.onload = function() {
                    img.style.display = '';
                    wrap.classList.add('has-feed');
                    placeholder.style.display = 'none';
                };
            } else {
                placeholder.textContent = 'Loading video...';
                placeholder.style.display = '';
                video.style.display = '';
                video.src = url;
                video.onerror = function() {
                    wrap.classList.remove('has-feed');
                    placeholder.style.display = '';
                    placeholder.textContent = 'Failed to load video';
                };
                video.onloadeddata = function() {
                    wrap.classList.add('has-feed');
                    placeholder.style.display = 'none';
                };
            }
        }
    }
    function run() {
        var cells = document.querySelectorAll('.grid-cell-webcam');
        cells.forEach(function(cell) {
            var key = getCellKey(cell);
            stopStream(key);
            updateCell(cell);
        });
    }
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', run);
    } else {
        run();
    }
    window.GLANCERF_webcam_refresh = function() {
        var cells = document.querySelectorAll('.grid-cell-webcam');
        cells.forEach(function(c) { stopStream(getCellKey(c)); });
        run();
    };
})();
