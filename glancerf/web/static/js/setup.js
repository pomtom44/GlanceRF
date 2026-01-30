(function() {
    var cfg = window.SETUP_CONFIG || {};
    var currentAspectRatio = (cfg.current_ratio != null ? cfg.current_ratio : '16:9');
    var currentOrientation = (cfg.current_orientation != null ? cfg.current_orientation : 'landscape');

function isSubmitButton(el) { return el && (el.type === 'submit' || (el.tagName === 'BUTTON' && el.getAttribute('type') === 'submit')); };
            // Store current aspect ratio and orientation
            let targetRatio = 16 / 9; // Initial ratio (width/height)
            let isDragging = false;
        
            function getDOMElements() {
                return {
                    gridColumnsInput: document.getElementById('grid_columns'),
                    gridRowsInput: document.getElementById('grid_rows'),
                    aspectRatioSelect: document.getElementById('aspect_ratio'),
                    orientationSelect: document.getElementById('orientation'),
                    columnsValue: document.getElementById('columns-value'),
                    rowsValue: document.getElementById('rows-value'),
                    previewSquare: document.getElementById('preview-square'),
                    previewContainer: document.getElementById('preview-square')?.parentElement,
                    sliderContainerInner: document.querySelector('.slider-container-inner'),
                    previewWrapper: document.querySelector('.preview-wrapper'),
                    rowSliderWrapper: document.querySelector('.slider-vertical-wrapper'),
                    sliderRotated: document.querySelector('.slider-vertical-rotated')
                };
            }
        
            // Function to calculate and set box dimensions. Portrait: lock height to fit screen, width follows. Landscape: lock width, height follows.
            function updateBoxDimensions() {
                const els = getDOMElements();
                if (!els.previewContainer || !els.previewSquare) return;
            
                const orientation = (els.orientationSelect && els.orientationSelect.value) || currentOrientation;
                const isPortrait = orientation === 'portrait';
                const containerWidth = els.previewContainer.offsetWidth;
                const maxHeightPx = Math.min(window.innerHeight * 0.55, 500);
            
                let boxWidth, boxHeight;
                if (isPortrait) {
                    // Portrait: fix height so preview fits on screen, width is derived (unlocked)
                    const displayRatio = 1 / targetRatio;
                    boxHeight = maxHeightPx;
                    boxWidth = boxHeight * displayRatio;
                } else {
                    // Landscape: fix width, height derived
                    if (containerWidth <= 0) return;
                    const displayRatio = targetRatio;
                    boxWidth = containerWidth;
                    boxHeight = containerWidth / displayRatio;
                }
            
                els.previewSquare.style.width = boxWidth + 'px';
                els.previewSquare.style.height = boxHeight + 'px';
            
                // In portrait, shrink preview container to box width so the vertical slider stays pinned to the preview
                if (els.previewContainer) {
                    if (isPortrait) {
                        els.previewContainer.style.width = boxWidth + 'px';
                        els.previewContainer.style.maxWidth = boxWidth + 'px';
                    } else {
                        els.previewContainer.style.width = '';
                        els.previewContainer.style.maxWidth = '';
                    }
                }
            
                // Column slider width matches preview box; align its right edge with the box (works for portrait and landscape)
                if (els.sliderContainerInner && els.previewWrapper) {
                    els.sliderContainerInner.style.width = boxWidth + 'px';
                    const wrapperRect = els.previewWrapper.getBoundingClientRect();
                    const boxRect = els.previewSquare.getBoundingClientRect();
                    const rightEdge = boxRect.right - wrapperRect.left;
                    els.sliderContainerInner.style.marginRight = (els.previewWrapper.offsetWidth - rightEdge) + 'px';
                }
            
                // Row slider height matches preview box height
                if (els.rowSliderWrapper && boxHeight > 0) {
                    els.rowSliderWrapper.style.height = boxHeight + 'px';
                    if (els.sliderRotated) {
                        els.sliderRotated.style.width = boxHeight + 'px';
                        els.sliderRotated.style.height = '8px';
                        els.sliderRotated.style.marginLeft = (-boxHeight / 2) + 'px';
                    }
                }
            }
        
            // Update display values for sliders and preview
            function updatePreview() {
                const els = getDOMElements();
                if (!els.gridColumnsInput || !els.gridRowsInput || !els.aspectRatioSelect || 
                    !els.columnsValue || !els.rowsValue || !els.previewSquare) {
                    return;
                }
            
                const columns = parseInt(els.gridColumnsInput.value);
                const rows = parseInt(els.gridRowsInput.value);
                const aspectRatio = els.aspectRatioSelect.value;
                if (els.orientationSelect) currentOrientation = els.orientationSelect.value;
            
                els.columnsValue.textContent = columns;
                els.rowsValue.textContent = rows;
            
                currentAspectRatio = aspectRatio;
                const ratioParts = aspectRatio.split(':');
                targetRatio = parseFloat(ratioParts[0]) / parseFloat(ratioParts[1]);
            
                // Set up grid
                els.previewSquare.style.gridTemplateColumns = `repeat(${columns}, 1fr)`;
                els.previewSquare.style.gridTemplateRows = `repeat(${rows}, 1fr)`;
            
                // Generate grid cells using DocumentFragment for better performance
                const fragment = document.createDocumentFragment();
                for (let i = 0; i < columns * rows; i++) {
                    const cell = document.createElement('div');
                    cell.className = 'preview-cell';
                    fragment.appendChild(cell);
                }
                els.previewSquare.innerHTML = '';
                els.previewSquare.appendChild(fragment);
            
                // Calculate and set box dimensions after DOM is ready
                requestAnimationFrame(function() {
                    updateBoxDimensions();
                    // Double-check after a short delay to ensure container has width
                    setTimeout(updateBoxDimensions, 50);
                });
            }
        
            // Function to initialize event listeners
            function initializeEventListeners() {
                const els = getDOMElements();
                if (!els.gridColumnsInput || !els.gridRowsInput || !els.aspectRatioSelect) {
                    return;
                }
            
                const currentColumnsValue = els.gridColumnsInput.value;
                const currentRowsValue = els.gridRowsInput.value;
                const currentAspectRatioValue = els.aspectRatioSelect.value;
                const currentOrientationValue = els.orientationSelect ? els.orientationSelect.value : 'landscape';
            
                const newGridColumnsInput = els.gridColumnsInput.cloneNode(true);
                const newGridRowsInput = els.gridRowsInput.cloneNode(true);
                const newAspectRatioSelect = els.aspectRatioSelect.cloneNode(true);
                const newOrientationSelect = els.orientationSelect ? els.orientationSelect.cloneNode(true) : null;
            
                newGridColumnsInput.value = currentColumnsValue;
                newGridRowsInput.value = currentRowsValue;
                newAspectRatioSelect.value = currentAspectRatioValue;
                if (newOrientationSelect) newOrientationSelect.value = currentOrientationValue;
            
                els.gridColumnsInput.parentNode.replaceChild(newGridColumnsInput, els.gridColumnsInput);
                els.gridRowsInput.parentNode.replaceChild(newGridRowsInput, els.gridRowsInput);
                els.aspectRatioSelect.parentNode.replaceChild(newAspectRatioSelect, els.aspectRatioSelect);
                if (els.orientationSelect && newOrientationSelect) {
                    els.orientationSelect.parentNode.replaceChild(newOrientationSelect, els.orientationSelect);
                }
            
                newGridColumnsInput.addEventListener('input', function() { updatePreview(); });
                newGridRowsInput.addEventListener('input', function() { updatePreview(); });
                newAspectRatioSelect.addEventListener('change', function() { updatePreview(); });
                if (newOrientationSelect) {
                    newOrientationSelect.addEventListener('change', function() { updatePreview(); });
                }
            
                // Track dragging state to prevent WebSocket updates during drag
                newGridColumnsInput.addEventListener('mousedown', function() {
                    isDragging = true;
                });
                newGridColumnsInput.addEventListener('mouseup', function() {
                    isDragging = false;
                });
                newGridRowsInput.addEventListener('mousedown', function() {
                    isDragging = true;
                });
                newGridRowsInput.addEventListener('mouseup', function() {
                    isDragging = false;
                });
            }
        
            // Update preview on window resize (debounced)
            let resizeTimeout;
            window.addEventListener('resize', function() {
                clearTimeout(resizeTimeout);
                resizeTimeout = setTimeout(updatePreview, 100);
            });
        
            function showSetupPage(num) {
                var page1 = document.getElementById('setup-page-1');
                var page2 = document.getElementById('setup-page-2');
                var page3 = document.getElementById('setup-page-3');
                var tab1 = document.getElementById('tab-page-1');
                var tab2 = document.getElementById('tab-page-2');
                var tab3 = document.getElementById('tab-page-3');
                if (page1) page1.classList.toggle('active', num === 1);
                if (page2) page2.classList.toggle('active', num === 2);
                if (page3) page3.classList.toggle('active', num === 3);
                if (tab1) tab1.classList.toggle('active', num === 1);
                if (tab2) tab2.classList.toggle('active', num === 2);
                if (tab3) tab3.classList.toggle('active', num === 3);
            }
            (function() {
                var nextBtn = document.getElementById('setup-next-btn');
                var nextBtn2 = document.getElementById('setup-next-btn-2');
                var backBtn = document.getElementById('setup-back-btn');
                var backBtn3 = document.getElementById('setup-back-btn-3');
                var tab1 = document.getElementById('tab-page-1');
                var tab2 = document.getElementById('tab-page-2');
                var tab3 = document.getElementById('tab-page-3');
                if (nextBtn) nextBtn.addEventListener('click', function() { showSetupPage(2); });
                if (nextBtn2) nextBtn2.addEventListener('click', function() { showSetupPage(3); });
                if (backBtn) backBtn.addEventListener('click', function() { showSetupPage(1); });
                if (backBtn3) backBtn3.addEventListener('click', function() { showSetupPage(2); });
                if (tab1) tab1.addEventListener('click', function() { showSetupPage(1); });
                if (tab2) tab2.addEventListener('click', function() { showSetupPage(2); });
                if (tab3) tab3.addEventListener('click', function() { showSetupPage(3); });
            })();
        
            // Initialize on page load
            function initializeSetup() {
                initializeEventListeners();
                updatePreview();
            }
        
            // Initialize immediately
            initializeSetup();
        
            // Connect to WebSocket for mirroring
            let ws = null;
            const urlParams = new URLSearchParams(window.location.search);
            const isDesktop = urlParams.get('desktop') === 'true' || window.navigator.userAgent.includes('QtWebEngine');
        
            if (isDesktop) {
                // Desktop app connects to /ws/desktop
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${protocol}//${window.location.host}/ws/desktop`;
                ws = new WebSocket(wsUrl);
            
                ws.onerror = function(error) {
                    console.error('Desktop WebSocket error (setup):', error);
                };
            
                ws.onclose = function() { };
            
                ws.onmessage = function(event) {
                    const message = JSON.parse(event.data);
                
                    if (message.type === 'config_update') {
                        // Navigate to main so we don't reload /setup (redirect may not have completed yet)
                        var path = (window.location.pathname || '/').replace(/\\/$/, '') || '/';
                        if (path === '/setup') {
                            window.location.href = '/';
                        } else {
                            window.location.reload();
                        }
                        return;
                    }
                
                    if (message.type === 'dom') {
                        if (message.data && message.data.html) {
                            var incomingUrl = message.data.url || '';
                            var incomingPath = (function() {
                                try {
                                    var p = new URL(incomingUrl, window.location.origin).pathname;
                                    return (p || '/').replace(/\\/$/, '') || '/';
                                } catch (e) {
                                    var a = document.createElement('a');
                                    a.href = incomingUrl;
                                    return (a.pathname || '/').replace(/\\/$/, '') || '/';
                                }
                            })();
                            var ourPath = (window.location.pathname || '/').replace(/\\/$/, '') || '/';
                            if (incomingPath !== ourPath) return;
                            if (message.data.formState) {
                                if (isSubmitButton(document.activeElement)) return;
                                for (const [id, value] of Object.entries(message.data.formState)) {
                                    const el = document.getElementById(id) || document.querySelector(`[name="${id}"]`);
                                    if (el) {
                                        if (el.type === 'checkbox' || el.type === 'radio') {
                                            el.checked = value;
                                        } else {
                                            el.value = value;
                                        }
                                    }
                                }
                                updatePreview();
                            }
                        }
                    }
                };
            
                ws.onopen = function() {
                    sendDesktopState();
                
                    // Monitor DOM changes and send updates
                    let updateScheduled = false;
                    const observer = new MutationObserver(function(mutations) {
                        if (!updateScheduled) {
                            updateScheduled = true;
                            requestAnimationFrame(function() {
                                scheduleUpdate('MutationObserver');
                                updateScheduled = false;
                            });
                        }
                    });
                
                    observer.observe(document.body, {
                        childList: true,
                        subtree: true,
                        attributes: true,
                        attributeOldValue: true
                    });
                
                    // Send state on user interactions (but not during slider dragging)
                    let interactionScheduled = false;
                    function scheduleUpdate(fromWhere) {
                        if (arguments.length && typeof arguments[0] === 'object' && arguments[0].type) fromWhere = arguments[0].type;
                        else fromWhere = fromWhere || '?';
                        if (isDragging) return;
                        if (isSubmitButton(document.activeElement)) return;
                        if (!interactionScheduled) {
                            interactionScheduled = true;
                            requestAnimationFrame(function() {
                                if (isSubmitButton(document.activeElement)) { interactionScheduled = false; return; }
                                sendDesktopState();
                                interactionScheduled = false;
                            });
                        }
                    }
                    function onClick(e) {
                        if (isSubmitButton(e.target)) return;
                        scheduleUpdate('click');
                    }
                    function onFocus(e) {
                        if (isSubmitButton(e.target)) return;
                        scheduleUpdate('focus');
                    }
                    function onMouseUp(e) {
                        if (isSubmitButton(e.target)) return;
                        setTimeout(function() { scheduleUpdate('mouseup'); }, 50);
                    }
                
                    document.addEventListener('click', onClick, true);
                    document.addEventListener('input', scheduleUpdate, true);
                    document.addEventListener('change', scheduleUpdate, true);
                    document.addEventListener('focus', onFocus, true);
                    document.addEventListener('mouseup', onMouseUp, true);
                };
            
                let lastSentHtml = '';
                let lastSentFormState = '';
            
                function sendDesktopState() {
                    if (ws && ws.readyState === WebSocket.OPEN) {
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
                    
                        const currentHtml = document.documentElement.outerHTML;
                        const currentFormState = JSON.stringify(formState);
                    
                        if (currentHtml !== lastSentHtml || currentFormState !== lastSentFormState) {
                            lastSentHtml = currentHtml;
                            lastSentFormState = currentFormState;
                            ws.send(JSON.stringify({
                                type: 'dom',
                                data: {
                                    html: currentHtml,
                                    url: window.location.href,
                                    formState: formState
                                }
                            }));
                        }
                    }
                }
            } else {
                // Web browser connects to /ws/browser for two-way mirroring
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${protocol}//${window.location.host}/ws/browser`;
                ws = new WebSocket(wsUrl);
            
                ws.onerror = function(error) {
                    console.error('Browser WebSocket error (setup):', error);
                };
            
                ws.onclose = function() { };
            
                ws.onmessage = function(event) {
                    const message = JSON.parse(event.data);
                
                    if (message.type === 'config_update') {
                        // Navigate to main so we don't reload /setup (redirect may not have completed yet)
                        var path = (window.location.pathname || '/').replace(/\\/$/, '') || '/';
                        if (path === '/setup') {
                            window.location.href = '/';
                        } else {
                            window.location.reload();
                        }
                        return;
                    }
                
                    if (message.type === 'dom') {
                        if (message.data && message.data.html) {
                            var incomingUrl = message.data.url || '';
                            var incomingPath = (function() {
                                try {
                                    var p = new URL(incomingUrl, window.location.origin).pathname;
                                    return (p || '/').replace(/\\/$/, '') || '/';
                                } catch (e) {
                                    var a = document.createElement('a');
                                    a.href = incomingUrl;
                                    return (a.pathname || '/').replace(/\\/$/, '') || '/';
                                }
                            })();
                            var ourPath = (window.location.pathname || '/').replace(/\\/$/, '') || '/';
                            if (incomingPath !== ourPath) return;
                            if (message.data.formState) {
                                if (isSubmitButton(document.activeElement)) return;
                                for (const [id, value] of Object.entries(message.data.formState)) {
                                    const el = document.getElementById(id) || document.querySelector(`[name="${id}"]`);
                                    if (el) {
                                        if (el.type === 'checkbox' || el.type === 'radio') {
                                            el.checked = value;
                                        } else {
                                            el.value = value;
                                        }
                                    }
                                }
                                updatePreview();
                            }
                        }
                    }
                };
            
                ws.onopen = function() {
                    sendBrowserState();
                
                    let updateScheduled = false;
                    const observer = new MutationObserver(function(mutations) {
                        if (!updateScheduled) {
                            updateScheduled = true;
                            requestAnimationFrame(function() {
                                scheduleUpdate('MutationObserver');
                                updateScheduled = false;
                            });
                        }
                    });
                
                    observer.observe(document.body, {
                        childList: true,
                        subtree: true,
                        attributes: true,
                        attributeOldValue: true
                    });
                
                    let interactionScheduled = false;
                    function scheduleUpdate(fromWhere) {
                        if (arguments.length && typeof arguments[0] === 'object' && arguments[0].type) fromWhere = arguments[0].type;
                        else fromWhere = fromWhere || '?';
                        if (isDragging) return;
                        if (isSubmitButton(document.activeElement)) return;
                        if (!interactionScheduled) {
                            interactionScheduled = true;
                            requestAnimationFrame(function() {
                                if (isSubmitButton(document.activeElement)) { interactionScheduled = false; return; }
                                sendBrowserState();
                                interactionScheduled = false;
                            });
                        }
                    }
                    function onBrowserClick(e) {
                        if (isSubmitButton(e.target)) return;
                        scheduleUpdate('click');
                    }
                    function onBrowserFocus(e) {
                        if (isSubmitButton(e.target)) return;
                        scheduleUpdate('focus');
                    }
                    function onBrowserMouseUp(e) {
                        if (isSubmitButton(e.target)) return;
                        setTimeout(function() { scheduleUpdate('mouseup'); }, 50);
                    }
                
                    document.addEventListener('click', onBrowserClick, true);
                    document.addEventListener('input', scheduleUpdate, true);
                    document.addEventListener('change', scheduleUpdate, true);
                    document.addEventListener('focus', onBrowserFocus, true);
                    document.addEventListener('mouseup', onBrowserMouseUp, true);
                };
            
                let lastSentHtml = '';
                let lastSentFormState = '';
            
                function sendBrowserState() {
                    if (ws && ws.readyState === WebSocket.OPEN) {
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
                    
                        const currentHtml = document.documentElement.outerHTML;
                        const currentFormState = JSON.stringify(formState);
                    
                        if (currentHtml !== lastSentHtml || currentFormState !== lastSentFormState) {
                            lastSentHtml = currentHtml;
                            lastSentFormState = currentFormState;
                            ws.send(JSON.stringify({
                                type: 'dom',
                                data: {
                                    html: currentHtml,
                                    url: window.location.href,
                                    formState: formState
                                }
                            }));
                        }
                    }
                }
            }
})();