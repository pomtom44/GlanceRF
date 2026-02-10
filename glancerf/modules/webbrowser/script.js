(function() {
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
    function updateCell(cell) {
        var wrap = cell.querySelector('.webbrowser_wrap');
        var frame = cell.querySelector('.webbrowser_frame');
        var placeholder = cell.querySelector('.webbrowser_placeholder');
        var openLink = cell.querySelector('.webbrowser_open_link');
        if (!wrap || !frame) return;
        var settings = getCellSettings(cell);
        var url = (settings.url || '').trim();
        var mode = (settings.mode || 'iframe').toLowerCase();
        if (!isAllowedUrl(url)) {
            wrap.classList.remove('has-url');
            wrap.classList.remove('mode-proxy');
            frame.removeAttribute('src');
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
        if (mode === 'proxy') wrap.classList.add('mode-proxy'); else wrap.classList.remove('mode-proxy');
        if (frame.getAttribute('src') !== src) frame.setAttribute('src', src);
    }
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
