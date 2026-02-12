(function() {
    var _originalConsoleError = console.error;
    function getCellSettings(cell) {
        var allSettings = window.GLANCERF_MODULE_SETTINGS || {};
        var r = cell.getAttribute('data-row');
        var c = cell.getAttribute('data-col');
        var key = (r != null && c != null) ? r + '_' + c : '';
        return (key && allSettings[key]) ? allSettings[key] : {};
    }
    function isAllowedUrl(url) {
        if (!url || typeof url !== 'string') return false;
        var t = url.trim().toLowerCase();
        return t.indexOf('http://') === 0 || t.indexOf('https://') === 0;
    }
    function showFrameBlockedOverlay() {
        var cells = document.querySelectorAll('.grid-cell-webbrowser .webbrowser_wrap.has-url:not(.mode-proxy)');
        cells.forEach(function(wrap) {
            var el = wrap.querySelector('.webbrowser_frame_blocked');
            if (el) el.style.display = 'flex';
        });
    }
    function updateCell(cell) {
        var wrap = cell.querySelector('.webbrowser_wrap');
        var frame = cell.querySelector('.webbrowser_frame');
        var placeholder = cell.querySelector('.webbrowser_placeholder');
        var openLink = cell.querySelector('.webbrowser_open_link');
        var frameBlocked = wrap ? wrap.querySelector('.webbrowser_frame_blocked') : null;
        if (!wrap || !frame) return;
        var settings = getCellSettings(cell);
        var url = (settings.url || '').trim();
        var mode = (settings.mode || 'iframe').toLowerCase();
        if (!isAllowedUrl(url)) {
            wrap.classList.remove('has-url');
            wrap.classList.remove('mode-proxy');
            frame.removeAttribute('src');
            if (frameBlocked) frameBlocked.style.display = 'none';
            if (placeholder) placeholder.style.display = '';
            if (openLink) { openLink.style.display = 'none'; openLink.href = '#'; }
            return;
        }
        wrap.classList.add('has-url');
        if (placeholder) placeholder.style.display = 'none';
        if (openLink) {
            openLink.href = url;
            openLink.style.display = '';
        }
        var src = (mode === 'proxy') ? '/api/webbrowser/proxy?url=' + encodeURIComponent(url) : url;
        if (mode === 'proxy') {
            wrap.classList.add('mode-proxy');
            if (frameBlocked) frameBlocked.style.display = 'none';
        } else {
            wrap.classList.remove('mode-proxy');
            if (frameBlocked) frameBlocked.style.display = 'flex';
        }
        if (frame.getAttribute('src') !== src) frame.setAttribute('src', src);
    }
    console.error = function() {
        var msg = Array.prototype.slice.call(arguments).join(' ');
        if (typeof msg === 'string' && (msg.indexOf('X-Frame-Options') !== -1 || msg.indexOf('sameorigin') !== -1) && (msg.indexOf('frame') !== -1 || msg.indexOf('Refused to display') !== -1)) {
            showFrameBlockedOverlay();
        }
        return _originalConsoleError.apply(console, arguments);
    };
    function run() {
        var cells = document.querySelectorAll('.grid-cell-webbrowser');
        cells.forEach(function(cell) { updateCell(cell); });
    }
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', run);
    } else {
        run();
    }
    window.GLANCERF_webbrowser_refresh = run;
})();
