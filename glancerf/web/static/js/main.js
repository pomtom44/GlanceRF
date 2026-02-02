        // Each view uses its own viewport sizing; no desktop/browser size sync.
        let ws = null;
        const urlParams = new URLSearchParams(window.location.search);
        const isDesktop = urlParams.get('desktop') === 'true' || window.navigator.userAgent.includes('QtWebEngine');
        
        // Check if current page should sync (only main dashboard)
        function shouldSyncPage() {
            const path = window.location.pathname;
            // Only sync on main dashboard page (/)
            return path === '/' || path === '';
        }
        
        // WebSocket lost warning and timer (top-left); reconnect every 10s
        let wsDisconnectedAt = null;
        let wsLostIntervalId = null;
        let wsReconnectIntervalId = null;
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
            wsDisconnectedAt = Date.now();
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
        
        if (isDesktop) {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/desktop`;
            console.log('Desktop connecting to WebSocket:', wsUrl);
            
            function attachDesktopHandlers() {
                ws.onerror = function(error) {
                    console.error('Desktop WebSocket error:', error);
                    showWsLostStartTimer(desktopReconnect);
                };
                ws.onclose = function(event) {
                    console.log('Desktop WebSocket closed:', event.code, event.reason);
                    showWsLostStartTimer(desktopReconnect);
                };
                ws.onmessage = function(event) {
                    const message = JSON.parse(event.data);
                    if (message.type === 'config_update') {
                        console.log('Config updated, reloading page...');
                        window.location.reload();
                        return;
                    }
                    if (message.type === 'update_available') {
                        showUpdateNotification(message.data);
                        return;
                    }
                    if (message.type === 'dom') return;
                };
                ws.onopen = function() {
                    console.log('Desktop app connected to mirroring server');
                    hideWsLostStopTimer();
                };
            }
            function desktopReconnect() {
                if (ws && ws.readyState === WebSocket.OPEN) return;
                console.log('Attempting to reconnect desktop WebSocket...');
                ws = new WebSocket(wsUrl);
                attachDesktopHandlers();
            }
            
            ws = new WebSocket(wsUrl);
            attachDesktopHandlers();
            
            // Cache last sent state to avoid sending duplicates
            let lastSentHtml = '';
            let lastSentFormState = '';
            let lastSentScrollState = '';
            let lastSentActiveElement = '';
            
            function sendDesktopState() {
                // Only sync on main dashboard page
                if (!shouldSyncPage()) return;
                
                if (ws && ws.readyState === WebSocket.OPEN) {
                    // Capture all form element values
                    const formState = {};
                    document.querySelectorAll('input, select, textarea').forEach(function(el) {
                        const id = el.id || el.name;
                        if (id) {
                            if (el.type === 'checkbox' || el.type === 'radio') {
                                formState[id] = el.checked;
                            } else {
                                formState[id] = el.value;
                            }
                        }
                    });
                    
                    // Capture scroll positions
                    const scrollState = {
                        x: window.scrollX,
                        y: window.scrollY
                    };
                    
                    // Capture active element details
                    let activeElementState = null;
                    if (document.activeElement) {
                        const el = document.activeElement;
                        activeElementState = {
                            tag: el.tagName,
                            id: el.id || null,
                            name: el.name || null,
                            type: el.type || null,
                            value: el.value || null,
                            checked: el.checked || null,
                            // For select elements, capture if dropdown is open
                            size: el.tagName === 'SELECT' ? el.size : null,
                            selectedIndex: el.tagName === 'SELECT' ? el.selectedIndex : null
                        };
                    }
                    
                    // Serialize for comparison
                    const currentHtml = document.documentElement.outerHTML;
                    const currentFormState = JSON.stringify(formState);
                    const currentScrollState = JSON.stringify(scrollState);
                    const currentActiveElement = JSON.stringify(activeElementState);
                    
                    // Only send if something actually changed
                    if (currentHtml !== lastSentHtml || 
                        currentFormState !== lastSentFormState || 
                        currentScrollState !== lastSentScrollState ||
                        currentActiveElement !== lastSentActiveElement) {
                        
                        // Update cache
                        lastSentHtml = currentHtml;
                        lastSentFormState = currentFormState;
                        lastSentScrollState = currentScrollState;
                        lastSentActiveElement = currentActiveElement;
                        
                        // Send current DOM state with all interactive states
                        ws.send(JSON.stringify({
                            type: 'dom',
                            data: {
                                html: currentHtml,
                                url: window.location.href,
                                formState: formState,
                                scrollState: scrollState,
                                activeElement: activeElementState
                            }
                        }));
                    }
                }
            }
        } else {
            // Web browser connects to /ws/browser for two-way mirroring
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/browser`;
            console.log('Browser connecting to WebSocket:', wsUrl);
            
            // Cache last sent state to avoid sending duplicates
            let lastSentHtml = '';
            let lastSentFormState = '';
            let lastSentScrollState = '';
            let lastSentActiveElement = '';
            
            // Function to send browser state updates
            function sendBrowserState() {
                // Only sync on main dashboard page
                if (!shouldSyncPage()) return;
                
                if (ws && ws.readyState === WebSocket.OPEN) {
                    // Capture all form element values
                    const formState = {};
                    document.querySelectorAll('input, select, textarea').forEach(function(el) {
                        const id = el.id || el.name;
                        if (id) {
                            if (el.type === 'checkbox' || el.type === 'radio') {
                                formState[id] = el.checked;
                            } else {
                                formState[id] = el.value;
                            }
                        }
                    });
                    
                    // Capture scroll positions
                    const scrollState = {
                        x: window.scrollX,
                        y: window.scrollY
                    };
                    
                    // Capture active element details
                    let activeElementState = null;
                    if (document.activeElement) {
                        const el = document.activeElement;
                        activeElementState = {
                            tag: el.tagName,
                            id: el.id || null,
                            name: el.name || null,
                            type: el.type || null,
                            value: el.value || null,
                            checked: el.checked || null,
                            // For select elements, capture if dropdown is open
                            size: el.tagName === 'SELECT' ? el.size : null,
                            selectedIndex: el.tagName === 'SELECT' ? el.selectedIndex : null
                        };
                    }
                    
                    // Serialize for comparison
                    const currentHtml = document.documentElement.outerHTML;
                    const currentFormState = JSON.stringify(formState);
                    const currentScrollState = JSON.stringify(scrollState);
                    const currentActiveElement = JSON.stringify(activeElementState);
                    
                    // Only send if something actually changed
                    if (currentHtml !== lastSentHtml || 
                        currentFormState !== lastSentFormState || 
                        currentScrollState !== lastSentScrollState ||
                        currentActiveElement !== lastSentActiveElement) {
                        
                        // Update cache
                        lastSentHtml = currentHtml;
                        lastSentFormState = currentFormState;
                        lastSentScrollState = currentScrollState;
                        lastSentActiveElement = currentActiveElement;
                        
                        // Send current DOM state with all interactive states
                        ws.send(JSON.stringify({
                            type: 'dom',
                            data: {
                                html: currentHtml,
                                url: window.location.href,
                                formState: formState,
                                scrollState: scrollState,
                                activeElement: activeElementState
                            }
                        }));
                    }
                }
            }
            
            function attachBrowserHandlers() {
                ws.onerror = function(error) {
                    console.error('Browser WebSocket error:', error);
                    showWsLostStartTimer(browserReconnect);
                };
                ws.onclose = function(event) {
                    console.log('Browser WebSocket closed:', event.code, event.reason);
                    showWsLostStartTimer(browserReconnect);
                };
                ws.onmessage = function(event) {
                    const message = JSON.parse(event.data);
                    if (message.type === 'config_update') {
                        console.log('Config updated, reloading page...');
                        window.location.reload();
                        return;
                    }
                    if (message.type === 'update_available') {
                        showUpdateNotification(message.data);
                        return;
                    }
                    if (message.type === 'dom') return;
                    if (message.type === 'state') {
                        if (message.data.grid_columns !== undefined || message.data.grid_rows !== undefined) {
                            location.reload();
                        }
                    }
                };
                ws.onopen = function() {
                    console.log('Browser connected to mirroring server');
                    hideWsLostStopTimer();
                };
            }
            function browserReconnect() {
                if (ws && ws.readyState === WebSocket.OPEN) return;
                console.log('Attempting to reconnect browser WebSocket...');
                ws = new WebSocket(wsUrl);
                attachBrowserHandlers();
            }
            
            ws = new WebSocket(wsUrl);
            attachBrowserHandlers();
        }
        
        // Keyboard shortcut: M opens menu (Setup, Layout editor, Modules, Manual Updates)
        document.addEventListener('keydown', function(event) {
            const isInputFocused = document.activeElement && (
                document.activeElement.tagName === 'INPUT' ||
                document.activeElement.tagName === 'TEXTAREA' ||
                document.activeElement.isContentEditable
            );
            if (isInputFocused) return;

            if (event.key === 'm' || event.key === 'M') {
                event.preventDefault();
                event.stopPropagation();
                var menu = document.getElementById('glancerf-menu');
                if (menu) menu.classList.toggle('open');
                return false;
            }
            if (event.key === 'Escape') {
                var menu = document.getElementById('glancerf-menu');
                if (menu && menu.classList.contains('open')) {
                    menu.classList.remove('open');
                    event.preventDefault();
                }
            }
        }, true);

        // Menu: overlay click closes
        (function() {
            var overlay = document.getElementById('glancerf-menu-overlay');
            if (overlay) {
                overlay.addEventListener('click', function() {
                    var menu = document.getElementById('glancerf-menu');
                    if (menu) menu.classList.remove('open');
                });
            }
        })();
        
        // Size container to viewport only; no sync with desktop or other clients.
        function applyViewportSize() {
            const container = document.getElementById('aspect-container');
            if (!container) return;
            container.style.width = '100vw';
            container.style.height = '100vh';
        }
        
        window.addEventListener('load', applyViewportSize);

                function showUpdateNotification(data) {
            var notif = document.getElementById('update-notification');
            var content = document.getElementById('update-notification-content');
            if (!notif || !content) return;
            var current = data.current_version || 'unknown';
            var latest = data.latest_version || 'unknown';
            var mode = data.update_mode || 'notify';
            var status = data.update_status;
            var updateMsg = data.update_message;
            var restartPending = data.restart_pending;
            var restartIn = data.restart_in_seconds;
            
            var msg = 'Update available: ' + current + ' → ' + latest;
            
            if (status === 'success') {
                msg = 'Update installed: ' + current + ' → ' + latest;
                if (restartPending) {
                    msg += ' (Restarting in ' + restartIn + ' seconds...)';
                } else {
                    msg += ' (Restart required)';
                }
                notif.style.backgroundColor = '#0f0';
            } else if (status === 'failed') {
                msg = 'Update failed: ' + (updateMsg || 'Unknown error');
                notif.style.backgroundColor = '#f00';
            } else if (mode === 'auto') {
                msg += ' (Auto-update in progress...)';
                notif.style.backgroundColor = '#ff0';
                notif.style.color = '#000';
            } else {
                msg += ' (Notification only)';
            }
            
            content.textContent = msg;
            notif.classList.add('show');
            
            // If restart is pending, update countdown
            if (restartPending && restartIn) {
                var countdown = restartIn;
                var countdownInterval = setInterval(function() {
                    countdown--;
                    if (countdown <= 0) {
                        clearInterval(countdownInterval);
                        msg = 'Update installed: ' + current + ' → ' + latest + ' (Restarting now...)';
                        content.textContent = msg;
                    } else {
                        msg = 'Update installed: ' + current + ' → ' + latest + ' (Restarting in ' + countdown + ' seconds...)';
                        content.textContent = msg;
                    }
                }, 1000);
            }
        }
        
        window.addEventListener('resize', applyViewportSize);
        
        document.addEventListener('visibilitychange', function() {
            if (!document.hidden) applyViewportSize();
        });
