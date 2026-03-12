// Read-only view: no desktop/browser sync. Connects to main server WebSocket for config_update (layout/module changes) and reloads.
(function() {
    'use strict';
    var mainPort = typeof window.GLANCERF_MAIN_PORT !== 'undefined' ? window.GLANCERF_MAIN_PORT : 8080;
    var protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
    var wsUrl = protocol + '//' + location.hostname + ':' + mainPort + '/ws/readonly';
    var ws;
    var reconnectDelay = 3000;
    var maxReconnectDelay = 60000;

    function connect() {
        try {
            ws = new WebSocket(wsUrl);
            ws.onmessage = function(event) {
                try {
                    var msg = JSON.parse(event.data);
                    if (msg && msg.type === 'config_update') {
                        window.location.reload();
                    }
                    if (msg && msg.type === 'aprs_update') {
                        window.dispatchEvent(new CustomEvent('glancerf_aprs_update'));
                    }
                } catch (e) {
                    if (typeof console !== 'undefined' && console.debug) console.debug('readonly WebSocket parse error', e);
                }
            };
            ws.onerror = function() {
                if (typeof console !== 'undefined' && console.debug) console.debug('readonly WebSocket error');
            };
            ws.onclose = function() {
                setTimeout(function() {
                    connect();
                    reconnectDelay = Math.min(reconnectDelay * 1.5, maxReconnectDelay);
                }, reconnectDelay);
            };
            ws.onopen = function() {
                reconnectDelay = 3000;
            };
        } catch (e) {
            if (typeof console !== 'undefined' && console.error) console.error('readonly WebSocket connect failed', e);
            setTimeout(function() {
                connect();
                reconnectDelay = Math.min(reconnectDelay * 1.5, maxReconnectDelay);
            }, reconnectDelay);
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
