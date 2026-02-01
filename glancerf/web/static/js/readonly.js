// Read-only view: no desktop/browser sync. Connects to main server WebSocket for config_update (layout/module changes) and reloads.
(function() {
    var mainPort = typeof window.GLANCERF_MAIN_PORT !== 'undefined' ? window.GLANCERF_MAIN_PORT : 8080;
    var wsUrl = 'ws://' + location.hostname + ':' + mainPort + '/ws/readonly';
    var ws;
    function connect() {
        try {
            ws = new WebSocket(wsUrl);
            ws.onmessage = function(event) {
                try {
                    var msg = JSON.parse(event.data);
                    if (msg && msg.type === 'config_update') {
                        window.location.reload();
                    }
                } catch (e) {}
            };
            ws.onclose = function() {
                setTimeout(connect, 3000);
            };
        } catch (e) {
            setTimeout(connect, 3000);
        }
    }
    connect();
})();

document.addEventListener('keydown', function(e) {
    e.preventDefault();
    e.stopPropagation();
    return false;
}, true);

document.addEventListener('keyup', function(e) {
    e.preventDefault();
    e.stopPropagation();
    return false;
}, true);

document.addEventListener('click', function(e) {
    e.preventDefault();
    e.stopPropagation();
    return false;
}, true);

document.addEventListener('contextmenu', function(e) {
    e.preventDefault();
    return false;
}, true);

document.onselectstart = function() {
    return false;
};

document.onmousedown = function() {
    return false;
};
