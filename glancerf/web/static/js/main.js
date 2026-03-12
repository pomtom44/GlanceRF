/* GlanceRF main display - WebSocket sync for desktop/browser mirroring */

(function () {
  'use strict';

  var ws = null;
  var urlParams = new URLSearchParams(window.location.search);
  var isDesktop = urlParams.get('desktop') === 'true' || window.navigator.userAgent.indexOf('QtWebEngine') !== -1;

  function shouldSyncPage() {
    var path = window.location.pathname;
    return path === '/' || path === '';
  }

  var wsDisconnectedAt = null;
  var wsLostIntervalId = null;
  var wsReconnectIntervalId = null;

  function formatDisconnectedTime(ms) {
    var s = Math.floor(ms / 1000);
    var m = Math.floor(s / 60);
    s = s % 60;
    return m + 'm ' + s + 's';
  }

  function updateWsLostTimer() {
    if (!wsDisconnectedAt) return;
    var el = document.getElementById('ws-lost-timer');
    if (el) el.textContent = 'Disconnected: ' + formatDisconnectedTime(Date.now() - wsDisconnectedAt);
  }

  function showWsLostStartTimer(reconnectFn) {
    var el = document.getElementById('ws-lost-warning');
    if (el) { el.classList.add('show'); el.style.display = 'block'; }
    if (!wsDisconnectedAt) wsDisconnectedAt = Date.now();
    if (!wsLostIntervalId) wsLostIntervalId = setInterval(updateWsLostTimer, 1000);
    updateWsLostTimer();
    if (reconnectFn && !wsReconnectIntervalId) {
      wsReconnectIntervalId = setInterval(reconnectFn, 10000);
      setTimeout(reconnectFn, 10000);
    }
  }

  function hideWsLostStopTimer() {
    var el = document.getElementById('ws-lost-warning');
    if (el) { el.classList.remove('show'); el.style.display = 'none'; }
    wsDisconnectedAt = null;
    if (wsLostIntervalId) { clearInterval(wsLostIntervalId); wsLostIntervalId = null; }
    if (wsReconnectIntervalId) { clearInterval(wsReconnectIntervalId); wsReconnectIntervalId = null; }
  }

  function showUpdateNotification(data) {
    var notif = document.getElementById('update-notification');
    var content = document.getElementById('update-notification-content');
    if (!notif || !content) return;
    var current = data.current_version || 'unknown';
    var latest = data.latest_version || 'unknown';
    var msg = 'Update available: ' + current + ' → ' + latest;
    if (data.docker_mode) {
      msg += ' (In Docker: pull new image and recreate container)';
    }
    content.textContent = msg;
    notif.classList.add('show');
  }

  function safeGetFormElement(id) {
    if (!id || typeof id !== 'string') return null;
    var el = document.getElementById(id);
    if (el) return el;
    if (typeof CSS !== 'undefined' && CSS.escape) {
      try {
        return document.querySelector('[name="' + CSS.escape(id) + '"]');
      } catch (e) {
        return null;
      }
    }
    var inputs = document.querySelectorAll('input, select, textarea');
    for (var i = 0; i < inputs.length; i++) {
      if (inputs[i].name === id) return inputs[i];
    }
    return null;
  }

  function collectFormState() {
    var formState = {};
    document.querySelectorAll('input, select, textarea').forEach(function (el) {
      var id = el.id || el.name;
      if (id) formState[id] = (el.type === 'checkbox' || el.type === 'radio') ? el.checked : el.value;
    });
    return formState;
  }

  function sendState() {
    if (!shouldSyncPage()) return;
    if (!ws || ws.readyState !== WebSocket.OPEN) return;
    var formState = collectFormState();
    var scrollState = { x: window.scrollX, y: window.scrollY };
    var activeEl = document.activeElement;
    var activeElementState = activeEl ? { tag: activeEl.tagName, id: activeEl.id, name: activeEl.name, type: activeEl.type, value: activeEl.value, checked: activeEl.checked } : null;
    var currentHtml = document.documentElement.outerHTML;
    var currentFormState = JSON.stringify(formState);
    var currentScrollState = JSON.stringify(scrollState);
    var currentActiveElement = JSON.stringify(activeElementState);
    if (currentHtml !== sendState.lastSentHtml || currentFormState !== sendState.lastSentFormState || currentScrollState !== sendState.lastSentScrollState || currentActiveElement !== sendState.lastSentActiveElement) {
      sendState.lastSentHtml = currentHtml;
      sendState.lastSentFormState = currentFormState;
      sendState.lastSentScrollState = currentScrollState;
      sendState.lastSentActiveElement = currentActiveElement;
      ws.send(JSON.stringify({ type: 'dom', data: { html: currentHtml, url: window.location.href, formState: formState, scrollState: scrollState, activeElement: activeElementState } }));
    }
  }

  document.addEventListener('DOMContentLoaded', function () {
    var container = document.getElementById('aspect-container');
    var grid = container && container.querySelector('.grid-layout');
    if (grid) grid.style.minHeight = '100%';
  });

  if (isDesktop) {
    var protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    var wsUrl = protocol + '//' + window.location.host + '/ws/desktop';

    function attachDesktopHandlers() {
      ws.onerror = function () { showWsLostStartTimer(desktopReconnect); };
      ws.onclose = function () { showWsLostStartTimer(desktopReconnect); };
      ws.onmessage = function (event) {
        try {
          var message = JSON.parse(event.data);
          if (message.type === 'config_update') { window.location.reload(); return; }
          if (message.type === 'update_available') { showUpdateNotification(message.data); return; }
          if (message.type === 'aprs_update') { window.dispatchEvent(new CustomEvent('glancerf_aprs_update')); return; }
          if (message.type === 'gpio_input' && message.data) {
            window.dispatchEvent(new CustomEvent('glancerf_gpio_input', { detail: message.data }));
          }
          if (message.type === 'dom') return;
        } catch (e) {
          if (typeof console !== 'undefined' && console.debug) console.debug('WebSocket message parse error', e);
        }
      };
      ws.onopen = function () { hideWsLostStopTimer(); };
    }

    function desktopReconnect() {
      if (ws && ws.readyState === WebSocket.OPEN) return;
      ws = new WebSocket(wsUrl);
      attachDesktopHandlers();
    }

    ws = new WebSocket(wsUrl);
    attachDesktopHandlers();
    setInterval(sendState, 1000);
  } else {
    var protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    var wsUrl = protocol + '//' + window.location.host + '/ws/browser';

    function applyDomUpdate(d) {
      if (!d || !d.html) return;
      var scrollState = d.scrollState || {};
      var formState = d.formState || {};
      document.open();
      document.write(d.html);
      document.close();
      if (scrollState.x !== undefined || scrollState.y !== undefined) {
        window.scrollTo(scrollState.x || 0, scrollState.y || 0);
      }
      Object.keys(formState).forEach(function (id) {
        var el = safeGetFormElement(id);
        if (el) {
          if (el.type === 'checkbox' || el.type === 'radio') el.checked = !!formState[id];
          else el.value = formState[id];
        }
      });
    }

    function attachBrowserHandlers() {
      ws.onerror = function () { showWsLostStartTimer(browserReconnect); };
      ws.onclose = function () { showWsLostStartTimer(browserReconnect); };
      ws.onmessage = function (event) {
        try {
          var message = JSON.parse(event.data);
          if (message.type === 'config_update') { window.location.reload(); return; }
          if (message.type === 'update_available') { showUpdateNotification(message.data); return; }
          if (message.type === 'aprs_update') { window.dispatchEvent(new CustomEvent('glancerf_aprs_update')); return; }
          if (message.type === 'gpio_input' && message.data) {
            window.dispatchEvent(new CustomEvent('glancerf_gpio_input', { detail: message.data }));
          }
          if (message.type === 'dom') {
            applyDomUpdate(message.data);
            return;
          }
          if (message.type === 'state' && message.data && (message.data.grid_columns !== undefined || message.data.grid_rows !== undefined)) {
            window.location.reload();
          }
        } catch (e) {
          if (typeof console !== 'undefined' && console.debug) console.debug('WebSocket message parse error', e);
        }
      };
      ws.onopen = function () { hideWsLostStopTimer(); };
    }

    function browserReconnect() {
      if (ws && ws.readyState === WebSocket.OPEN) return;
      ws = new WebSocket(wsUrl);
      attachBrowserHandlers();
    }

    ws = new WebSocket(wsUrl);
    attachBrowserHandlers();
    setInterval(sendState, 1000);
  }
})();
