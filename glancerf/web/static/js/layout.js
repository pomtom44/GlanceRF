(function() {
    var cfg = window.LAYOUT_CONFIG || {};
    var MODULE_SETTINGS_BY_CELL = cfg.module_settings_by_cell || {};
    var MODULES_SETTINGS_SCHEMA = cfg.modules_settings_schema || {};
    window.GLANCERF_SETUP_CALLSIGN = cfg.setup_callsign != null ? cfg.setup_callsign : '';
    window.GLANCERF_SETUP_LOCATION = cfg.setup_location != null ? cfg.setup_location : '';
    var gridColumns = Number(cfg.grid_columns) || 3;
    var gridRows = Number(cfg.grid_rows) || 3;

    function stripTrailingSlash(s) {
        var p = (s == null || s === '') ? '/' : String(s);
        return (p.length > 1 && p.charAt(p.length - 1) === '/') ? p.slice(0, -1) : p;
    }

var currentDesktopWidth = 0;
            var currentDesktopHeight = 0;

            function updateCellSettings(cellEl) {
                var row = cellEl.getAttribute('data-row');
                var col = cellEl.getAttribute('data-col');
                var cellKey = row + '_' + col;
                var select = cellEl.querySelector('.cell-widget-select');
                var moduleId = select ? select.value : '';
                var container = cellEl.querySelector('.cell-module-settings');
                if (!container) return;
                container.innerHTML = '';
                var schema = MODULES_SETTINGS_SCHEMA[moduleId];
                if (!schema || schema.length === 0) return;
                var vals = MODULE_SETTINGS_BY_CELL[cellKey] || {};
                var inner = document.createElement('div');
                inner.className = 'cell-module-settings-inner';
                schema.forEach(function(s) {
                    var cur = vals[s.id] !== undefined ? vals[s.id] : (s.default !== undefined ? s.default : '');
                    if (!cur || cur === '') {
                        if (s.id === 'callsign' && window.GLANCERF_SETUP_CALLSIGN) {
                            cur = window.GLANCERF_SETUP_CALLSIGN;
                        } else if ((s.id === 'location' || s.id === 'grid') && window.GLANCERF_SETUP_LOCATION) {
                            cur = window.GLANCERF_SETUP_LOCATION;
                        }
                    }
                    var label = document.createElement('label');
                    label.className = 'cell-setting-label';
                    label.textContent = s.label;
                    inner.appendChild(label);
                    if (s.type === 'select') {
                        var opts = s.options || [];
                        if (s.optionsBySource && s.parentSettingId) {
                            var parentVal = vals[s.parentSettingId];
                            if (parentVal === undefined || parentVal === '' || !s.optionsBySource[parentVal])
                                parentVal = Object.keys(s.optionsBySource)[0];
                            opts = s.optionsBySource[parentVal] || opts;
                            var curInOpts = opts.some(function(opt) { return String(opt.value) === String(cur); });
                            if (!curInOpts && opts.length && opts[0].value !== undefined) cur = opts[0].value;
                        }
                        var sel = document.createElement('select');
                        sel.className = 'cell-setting-select';
                        sel.setAttribute('name', 'ms_' + row + '_' + col + '__' + s.id);
                        if (s.optionsBySource && s.parentSettingId) {
                            sel.setAttribute('data-parent-setting-id', s.parentSettingId);
                            sel.setAttribute('data-options-by-source', JSON.stringify(s.optionsBySource));
                        }
                        opts.forEach(function(opt) {
                            var op = document.createElement('option');
                            op.value = opt.value;
                            op.textContent = opt.label;
                            if (String(opt.value) === String(cur)) op.selected = true;
                            sel.appendChild(op);
                        });
                        inner.appendChild(sel);
                    } else if (s.type === 'number' || s.type === 'text') {
                        var inp = document.createElement('input');
                        inp.type = s.type;
                        inp.className = 'cell-setting-select';
                        inp.setAttribute('name', 'ms_' + row + '_' + col + '__' + s.id);
                        inp.value = cur;
                        if (s.type === 'number') {
                            if (s.min !== undefined) inp.min = s.min;
                            if (s.max !== undefined) inp.max = s.max;
                        }
                        inner.appendChild(inp);
                    } else if (s.type === 'range') {
                        var wrap = document.createElement('div');
                        wrap.className = 'cell-setting-range-wrap';
                        wrap.style.display = 'flex';
                        wrap.style.alignItems = 'center';
                        wrap.style.gap = '8px';
                        var inp = document.createElement('input');
                        inp.type = 'range';
                        inp.className = 'cell-setting-select';
                        inp.setAttribute('name', 'ms_' + row + '_' + col + '__' + s.id);
                        inp.value = cur;
                        if (s.min !== undefined) inp.min = s.min;
                        if (s.max !== undefined) inp.max = s.max;
                        var valSpan = document.createElement('span');
                        valSpan.style.minWidth = '2.5em';
                        valSpan.textContent = inp.value + (s.unit || '');
                        inp.addEventListener('input', function() { valSpan.textContent = inp.value + (s.unit || ''); });
                        wrap.appendChild(inp);
                        wrap.appendChild(valSpan);
                        inner.appendChild(wrap);
                    }
                });
                container.appendChild(inner);
            }

            function updateAllCellSettings() {
                document.querySelectorAll('.grid-cell:not(.hidden)').forEach(updateCellSettings);
            }
        
            function enforceAspectRatio() {
                const container = document.getElementById('aspect-container');
                if (!container) return;
                container.style.width = '';
                container.style.height = '';
                container.style.maxWidth = '';
                container.style.maxHeight = '';
            }
        
            // Enforce on load and resize (with debounce for resize)
            let resizeTimeout;
            function debouncedEnforceAspectRatio() {
                clearTimeout(resizeTimeout);
                resizeTimeout = setTimeout(enforceAspectRatio, 50);
            }
        
            window.addEventListener('load', function() {
                enforceAspectRatio();
                updateAllCellSettings();
                setTimeout(function() { enforceAspectRatio(); updateAllCellSettings(); }, 100);
            });
            document.addEventListener('change', function(e) {
                if (e.target && e.target.classList && e.target.classList.contains('cell-widget-select')) {
                    var cell = e.target.closest('.grid-cell');
                    if (cell) updateCellSettings(cell);
                }
                if (e.target && e.target.classList && e.target.classList.contains('cell-setting-select') && e.target.name && e.target.getAttribute('name').indexOf('__') >= 0) {
                    var container = e.target.closest('.cell-module-settings');
                    if (!container) return;
                    var name = e.target.getAttribute('name');
                    var settingId = name.slice(name.indexOf('__') + 2);
                    var dependent = container.querySelector('.cell-setting-select[data-parent-setting-id="' + settingId + '"]');
                    if (!dependent || !dependent.getAttribute('data-options-by-source')) return;
                    var optionsBySource = JSON.parse(dependent.getAttribute('data-options-by-source'));
                    var newParentVal = e.target.value;
                    var opts = optionsBySource[newParentVal];
                    if (!opts || !opts.length) return;
                    var cur = dependent.value;
                    var curInOpts = opts.some(function(opt) { return String(opt.value) === String(cur); });
                    if (!curInOpts) cur = opts[0].value;
                    dependent.innerHTML = '';
                    opts.forEach(function(opt) {
                        var op = document.createElement('option');
                        op.value = opt.value;
                        op.textContent = opt.label;
                        if (String(opt.value) === String(cur)) op.selected = true;
                        dependent.appendChild(op);
                    });
                    dependent.value = cur;
                }
            });
            window.addEventListener('resize', debouncedEnforceAspectRatio);
        
            // Also enforce when page becomes visible (in case it was hidden during config change)
            document.addEventListener('visibilitychange', function() {
                if (!document.hidden) {
                    setTimeout(enforceAspectRatio, 100);
                }
            });
        
            // Expand/Contract functionality
            function getCell(row, col) {
                return document.querySelector(`.grid-cell[data-row="${row}"][data-col="${col}"]`);
            }
        
            function isPrimaryCell(row, col) {
                // Check if this cell is a primary cell (not hidden and has colspan/rowspan > 1 or is visible)
                const cell = getCell(row, col);
                if (!cell || cell.classList.contains('hidden')) {
                    return false;
                }
                const colspan = parseInt(cell.dataset.colspan) || 1;
                const rowspan = parseInt(cell.dataset.rowspan) || 1;
                // If it has spans > 1, it's a primary cell of an expansion
                // If it's hidden, it's not a primary cell
                return !cell.classList.contains('hidden');
            }
        
            function getPrimaryCellForPosition(row, col) {
                // Find which primary cell (if any) owns this position
                // Check all visible cells to see if this position is within their span
                const allCells = document.querySelectorAll('.grid-cell:not(.hidden)');
                for (let cell of allCells) {
                    const cellRow = parseInt(cell.dataset.row);
                    const cellCol = parseInt(cell.dataset.col);
                    const colspan = parseInt(cell.dataset.colspan) || 1;
                    const rowspan = parseInt(cell.dataset.rowspan) || 1;
                
                    // Check if (row, col) is within this cell's span
                    if (row >= cellRow && row < cellRow + rowspan &&
                        col >= cellCol && col < cellCol + colspan) {
                        // If it's the primary cell itself, return null (can't expand into own primary)
                        if (row === cellRow && col === cellCol) {
                            return null;
                        }
                        // Otherwise, return the primary cell that owns this position
                        return {row: cellRow, col: cellCol, cell: cell};
                    }
                }
                return null;
            }
        
            function resetCellExpansion(primaryRow, primaryCol) {
                // Reset a cell's expansion back to 1x1 and show all its merged cells
                const cell = getCell(primaryRow, primaryCol);
                if (!cell) return;
            
                const colspan = parseInt(cell.dataset.colspan) || 1;
                const rowspan = parseInt(cell.dataset.rowspan) || 1;
            
                // Show all cells that were merged into this one
                for (let r = primaryRow; r < primaryRow + rowspan; r++) {
                    for (let c = primaryCol; c < primaryCol + colspan; c++) {
                        if (r !== primaryRow || c !== primaryCol) {
                            showCell(r, c);
                        }
                    }
                }
            
                // Reset the span to 1x1
                updateCellSpan(cell, 1, 1);
            }
        
            function updateCellSpan(cell, colspan, rowspan) {
                cell.setAttribute('data-colspan', colspan);
                cell.setAttribute('data-rowspan', rowspan);
                cell.style.gridColumn = `span ${colspan}`;
                cell.style.gridRow = `span ${rowspan}`;
            
                // Update button visibility
                const contractLeft = cell.querySelector('.contract-left');
                const contractTop = cell.querySelector('.contract-top');
                const expandRight = cell.querySelector('.expand-right');
                const expandDown = cell.querySelector('.expand-down');
            
                contractLeft.classList.toggle('contract-disabled', colspan <= 1);
                contractTop.classList.toggle('contract-disabled', rowspan <= 1);

                // Hide expand buttons if at grid edge
                const maxCol = gridColumns;
                const maxRow = gridRows;
                const cellCol = parseInt(cell.dataset.col);
                const cellRow = parseInt(cell.dataset.row);
            
                expandRight.style.display = (cellCol + colspan < maxCol) ? 'flex' : 'none';
                expandDown.style.display = (cellRow + rowspan < maxRow) ? 'flex' : 'none';
            
                // Dropdown is always centered horizontally and pinned to top
                // No need to change alignment based on span
            }
        
            function hideCell(row, col) {
                const cell = getCell(row, col);
                if (cell) {
                    cell.classList.add('hidden');
                }
            }
        
            function showCell(row, col) {
                const cell = getCell(row, col);
                if (cell) {
                    cell.classList.remove('hidden');
                }
            }
        
            // Handle expand/contract button clicks
            document.addEventListener('click', function(event) {
                if (event.target.classList.contains('expand-btn')) {
                    const btn = event.target;
                    const row = parseInt(btn.dataset.row);
                    const col = parseInt(btn.dataset.col);
                    const direction = btn.dataset.direction;
                    const cell = getCell(row, col);
                
                    if (!cell) return;
                
                    const currentColspan = parseInt(cell.dataset.colspan) || 1;
                    const currentRowspan = parseInt(cell.dataset.rowspan) || 1;
                
                    if (direction === 'right') {
                        const targetCol = col + currentColspan;
                        // Check all cells in the target column that are covered by the current rowspan
                        let canExpand = true;
                        const cellsToHide = [];
                        const primaryCellsToReset = new Set();
                    
                        for (let r = row; r < row + currentRowspan; r++) {
                            const targetCell = getCell(r, targetCol);
                            if (!targetCell || targetCell.classList.contains('hidden')) {
                                canExpand = false;
                                break;
                            }
                        
                            // Check if this position is owned by a primary cell
                            const owner = getPrimaryCellForPosition(r, targetCol);
                            if (owner) {
                                // This position is part of another expansion
                                // We need to reset that expansion first
                                const ownerKey = `${owner.row}_${owner.col}`;
                                if (!primaryCellsToReset.has(ownerKey)) {
                                    primaryCellsToReset.add(ownerKey);
                                    resetCellExpansion(owner.row, owner.col);
                                }
                            }
                        
                            // Mark this cell to be hidden
                            cellsToHide.push({row: r, col: targetCol});
                        }
                    
                        if (canExpand) {
                            // Hide all marked cells
                            cellsToHide.forEach(function(pos) {
                                hideCell(pos.row, pos.col);
                            });
                            updateCellSpan(cell, currentColspan + 1, currentRowspan);
                        }
                    } else if (direction === 'down') {
                        const targetRow = row + currentRowspan;
                        // Check all cells in the target row that are covered by the current colspan
                        let canExpand = true;
                        const cellsToHide = [];
                        const primaryCellsToReset = new Set();
                    
                        for (let c = col; c < col + currentColspan; c++) {
                            const targetCell = getCell(targetRow, c);
                            if (!targetCell || targetCell.classList.contains('hidden')) {
                                canExpand = false;
                                break;
                            }
                        
                            // Check if this position is owned by a primary cell
                            const owner = getPrimaryCellForPosition(targetRow, c);
                            if (owner) {
                                // This position is part of another expansion
                                // We need to reset that expansion first
                                const ownerKey = `${owner.row}_${owner.col}`;
                                if (!primaryCellsToReset.has(ownerKey)) {
                                    primaryCellsToReset.add(ownerKey);
                                    resetCellExpansion(owner.row, owner.col);
                                }
                            }
                        
                            // Mark this cell to be hidden
                            cellsToHide.push({row: targetRow, col: c});
                        }
                    
                        if (canExpand) {
                            // Hide all marked cells
                            cellsToHide.forEach(function(pos) {
                                hideCell(pos.row, pos.col);
                            });
                            updateCellSpan(cell, currentColspan, currentRowspan + 1);
                        }
                    }
                } else if (event.target.classList.contains('contract-btn')) {
                    const btn = event.target;
                    if (btn.classList.contains('contract-disabled')) return;
                    const row = parseInt(btn.dataset.row);
                    const col = parseInt(btn.dataset.col);
                    const direction = btn.dataset.direction;
                    const cell = getCell(row, col);
                
                    if (!cell) return;
                
                    const currentColspan = parseInt(cell.dataset.colspan) || 1;
                    const currentRowspan = parseInt(cell.dataset.rowspan) || 1;
                
                    if (direction === 'left' && currentColspan > 1) {
                        // Show the rightmost column of cells and contract
                        const showCol = col + currentColspan - 1;
                        for (let r = row; r < row + currentRowspan; r++) {
                            showCell(r, showCol);
                        }
                        updateCellSpan(cell, currentColspan - 1, currentRowspan);
                    } else if (direction === 'top' && currentRowspan > 1) {
                        // Show the bottommost row of cells and contract
                        const showRow = row + currentRowspan - 1;
                        for (let c = col; c < col + currentColspan; c++) {
                            showCell(showRow, c);
                        }
                        updateCellSpan(cell, currentColspan, currentRowspan - 1);
                    }
                }
            });
        
            // Initialize cell spans and button visibility, and hide merged cells
            document.querySelectorAll('.grid-cell').forEach(function(cell) {
                const row = parseInt(cell.dataset.row);
                const col = parseInt(cell.dataset.col);
                const colspan = parseInt(cell.dataset.colspan) || 1;
                const rowspan = parseInt(cell.dataset.rowspan) || 1;
            
                // Apply the span
                updateCellSpan(cell, colspan, rowspan);
            
                // Hide cells that are merged into this one
                for (let r = row; r < row + rowspan; r++) {
                    for (let c = col; c < col + colspan; c++) {
                        if (r !== row || c !== col) {
                            const mergedCell = getCell(r, c);
                            if (mergedCell) {
                                hideCell(r, c);
                            }
                        }
                    }
                }
            });
        
            // Save button handler
            document.getElementById('save-button').addEventListener('click', async function() {
                // Collect all cell values and span information
                const layout = [];
                const spans = {};  // Store span info: "row_col" -> {colspan, rowspan}
                const rows = gridRows;
                const cols = gridColumns;
            
                // Initialize 2D array
                for (let row = 0; row < rows; row++) {
                    layout[row] = [];
                    for (let col = 0; col < cols; col++) {
                        layout[row][col] = '';
                    }
                }
            
                // Fill with selected values from visible cells only
                // Hidden cells (merged into others) will remain empty
                document.querySelectorAll('.grid-cell:not(.hidden)').forEach(function(cell) {
                    const row = parseInt(cell.dataset.row);
                    const col = parseInt(cell.dataset.col);
                    const colspan = parseInt(cell.dataset.colspan) || 1;
                    const rowspan = parseInt(cell.dataset.rowspan) || 1;
                    const select = cell.querySelector('.cell-widget-select');
                    if (select) {
                        const value = select.value;
                        // Ensure row exists in layout array
                        if (!layout[row]) {
                            layout[row] = [];
                        }
                        // Set the value for the primary cell
                        layout[row][col] = value;
                        // Save span information if cell is expanded
                        if (colspan > 1 || rowspan > 1) {
                            spans[`${row}_${col}`] = {colspan: colspan, rowspan: rowspan};
                        }
                        // Mark all merged cells as empty (they're hidden)
                        for (let r = row; r < row + rowspan; r++) {
                            if (!layout[r]) {
                                layout[r] = [];
                            }
                            for (let c = col; c < col + colspan; c++) {
                                if (r !== row || c !== col) {
                                    layout[r][c] = '';
                                }
                            }
                        }
                    }
                });

                // Collect module settings by cell (name format: ms_<row>_<col>__<setting_id>)
                const module_settings = {};
                document.querySelectorAll('[name^="ms_"]').forEach(function(el) {
                    const name = el.getAttribute('name');
                    if (!name || name.indexOf('__') === -1) return;
                    const i = name.indexOf('__');
                    const cellPart = name.slice(3, i);
                    const settingId = name.slice(i + 2);
                    if (cellPart && settingId) {
                        if (!module_settings[cellPart]) module_settings[cellPart] = {};
                        module_settings[cellPart][settingId] = el.value || '';
                    }
                });
            
                // Send to server
                try {
                    const response = await fetch('/layout', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ layout: layout, spans: spans, module_settings: module_settings })
                    });
                
                    if (response.ok) {
                        // Redirect to main display
                        window.location.href = '/';
                    } else {
                        alert('Error saving layout');
                    }
                } catch (error) {
                    console.error('Error:', error);
                    alert('Error saving layout');
                }
            });
        
            function sendDesktopSize() {
                if (ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({ type: 'desktop_size', width: window.innerWidth, height: window.innerHeight }));
                }
            }
            let ws = null;
            const urlParams = new URLSearchParams(window.location.search);
            const isDesktop = urlParams.get('desktop') === 'true' || window.navigator.userAgent.includes('QtWebEngine');
        
            if (isDesktop) {
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${protocol}//${window.location.host}/ws/desktop`;
                console.log('Desktop connecting to WebSocket (layout):', wsUrl);
                ws = new WebSocket(wsUrl);
            
                ws.onerror = function(error) {
                    console.error('Desktop WebSocket error (layout):', error);
                };
            
                ws.onclose = function(event) {
                    console.log('Desktop WebSocket closed (layout):', event.code, event.reason);
                };
            
                // Desktop receives updates from browsers
                ws.onmessage = function(event) {
                    const message = JSON.parse(event.data);
                
                    if (message.type === 'config_update') {
                        console.log('Config updated, reloading page...');
                        window.location.reload();
                        return;
                    }
                    if (message.type === 'state') {
                        if (message.data.desktop_width !== undefined && message.data.desktop_height !== undefined) {
                            currentDesktopWidth = message.data.desktop_width || 0;
                            currentDesktopHeight = message.data.desktop_height || 0;
                        } else {
                            currentDesktopWidth = 0;
                            currentDesktopHeight = 0;
                        }
                        enforceAspectRatio();
                        return;
                    }
                    if (message.type === 'dom') {
                        // Layout editor should not receive DOM updates - only main dashboard syncs
                        return;
                        
                        if (message.data && message.data.html) {
                            var incomingUrl = message.data.url || '';
                            var incomingPath = (function() {
                                try {
                                    var p = new URL(incomingUrl, window.location.origin).pathname;
                                    return stripTrailingSlash(p) || '/';
                                } catch (e) {
                                    var a = document.createElement('a');
                                    a.href = incomingUrl;
                                    return stripTrailingSlash(a.pathname) || '/';
                                }
                            })();
                            var ourPath = stripTrailingSlash(window.location.pathname) || '/';
                            if (incomingPath !== ourPath) return;
                        
                            const parser = new DOMParser();
                            const newDoc = parser.parseFromString(message.data.html, 'text/html');
                            document.documentElement.innerHTML = newDoc.documentElement.innerHTML;
                        
                            if (message.data.formState) {
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
                            }
                        
                            if (message.data.scrollState) {
                                window.scrollTo(message.data.scrollState.x, message.data.scrollState.y);
                            }
                        
                            if (message.data.activeElement) {
                                const ae = message.data.activeElement;
                                let element = null;
                                if (ae.id) {
                                    element = document.getElementById(ae.id);
                                } else if (ae.name) {
                                    element = document.querySelector(`[name="${ae.name}"]`);
                                }
                            
                                if (element) {
                                    if (ae.value !== null && element.value !== undefined) {
                                        element.value = ae.value;
                                    }
                                    if (ae.checked !== null && element.checked !== undefined) {
                                        element.checked = ae.checked;
                                    }
                                    if (element.tagName === 'SELECT' && ae.selectedIndex !== null) {
                                        element.selectedIndex = ae.selectedIndex;
                                    }
                                    setTimeout(function() {
                                        element.focus();
                                        if (element.tagName === 'SELECT' && ae.size !== null && ae.size > 1) {
                                            element.size = Math.min(ae.size, element.options.length);
                                            element.style.position = 'relative';
                                            element.style.zIndex = '9999';
                                        }
                                    }, 10);
                                }
                            }
                        
                            setTimeout(function() {
                                enforceAspectRatio();
                            }, 100);
                        }
                    }
                };
            
                ws.onopen = function() {
                    console.log('Desktop app connected to mirroring server (layout configurator)');
                    sendDesktopSize();
                    var layoutDesktopResizeTimeout;
                    window.addEventListener('resize', function() {
                        clearTimeout(layoutDesktopResizeTimeout);
                        layoutDesktopResizeTimeout = setTimeout(sendDesktopSize, 100);
                    });
                    sendDesktopState();
                
                    let updateScheduled = false;
                    const observer = new MutationObserver(function(mutations) {
                        if (!updateScheduled) {
                            updateScheduled = true;
                            requestAnimationFrame(function() {
                                sendDesktopState();
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
                    function scheduleUpdate() {
                        if (!interactionScheduled) {
                            interactionScheduled = true;
                            requestAnimationFrame(function() {
                                sendDesktopState();
                                interactionScheduled = false;
                            });
                        }
                    }
                
                    document.addEventListener('click', scheduleUpdate, true);
                    document.addEventListener('input', scheduleUpdate, true);
                    document.addEventListener('change', scheduleUpdate, true);
                    document.addEventListener('focus', scheduleUpdate, true);
                    document.addEventListener('mousedown', scheduleUpdate, true);
                    document.addEventListener('mouseup', scheduleUpdate, true);
                    document.addEventListener('keydown', scheduleUpdate, true);
                    document.addEventListener('keyup', scheduleUpdate, true);
                };
            
                let lastSentHtml = '';
                let lastSentFormState = '';
                let lastSentScrollState = '';
                let lastSentActiveElement = '';
            
                function sendDesktopState() {
                    // Layout editor should not sync DOM - only main dashboard syncs
                    return;
                    
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
                    
                        const scrollState = {
                            x: window.scrollX,
                            y: window.scrollY
                        };
                    
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
                                size: el.tagName === 'SELECT' ? el.size : null,
                                selectedIndex: el.tagName === 'SELECT' ? el.selectedIndex : null
                            };
                        }
                    
                        const currentHtml = document.documentElement.outerHTML;
                        const currentFormState = JSON.stringify(formState);
                        const currentScrollState = JSON.stringify(scrollState);
                        const currentActiveElement = JSON.stringify(activeElementState);
                    
                        if (currentHtml !== lastSentHtml || 
                            currentFormState !== lastSentFormState || 
                            currentScrollState !== lastSentScrollState ||
                            currentActiveElement !== lastSentActiveElement) {
                        
                            lastSentHtml = currentHtml;
                            lastSentFormState = currentFormState;
                            lastSentScrollState = currentScrollState;
                            lastSentActiveElement = currentActiveElement;
                        
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
                console.log('Browser connecting to WebSocket (layout):', wsUrl);
                ws = new WebSocket(wsUrl);
            
                ws.onerror = function(error) {
                    console.error('Browser WebSocket error (layout):', error);
                };
            
                ws.onclose = function(event) {
                    console.log('Browser WebSocket closed (layout):', event.code, event.reason);
                };
            
                let lastSentHtml = '';
                let lastSentFormState = '';
                let lastSentScrollState = '';
                let lastSentActiveElement = '';
            
                function sendBrowserState() {
                    // Layout editor should not sync DOM - only main dashboard syncs
                    return;
                    
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
                    
                        const scrollState = {
                            x: window.scrollX,
                            y: window.scrollY
                        };
                    
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
                                size: el.tagName === 'SELECT' ? el.size : null,
                                selectedIndex: el.tagName === 'SELECT' ? el.selectedIndex : null
                            };
                        }
                    
                        const currentHtml = document.documentElement.outerHTML;
                        const currentFormState = JSON.stringify(formState);
                        const currentScrollState = JSON.stringify(scrollState);
                        const currentActiveElement = JSON.stringify(activeElementState);
                    
                        if (currentHtml !== lastSentHtml || 
                            currentFormState !== lastSentFormState || 
                            currentScrollState !== lastSentScrollState ||
                            currentActiveElement !== lastSentActiveElement) {
                        
                            lastSentHtml = currentHtml;
                            lastSentFormState = currentFormState;
                            lastSentScrollState = currentScrollState;
                            lastSentActiveElement = currentActiveElement;
                        
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
            
                ws.onmessage = function(event) {
                    const message = JSON.parse(event.data);
                
                    if (message.type === 'config_update') {
                        console.log('Config updated, reloading page...');
                        window.location.reload();
                        return;
                    }
                    if (message.type === 'state') {
                        if (message.data.desktop_width !== undefined && message.data.desktop_height !== undefined) {
                            currentDesktopWidth = message.data.desktop_width || 0;
                            currentDesktopHeight = message.data.desktop_height || 0;
                        } else {
                            currentDesktopWidth = 0;
                            currentDesktopHeight = 0;
                        }
                        enforceAspectRatio();
                        return;
                    }
                    if (message.type === 'dom') {
                        // Layout editor should not receive DOM updates - only main dashboard syncs
                        return;
                        
                        if (message.data && message.data.html) {
                            var incomingUrl = message.data.url || '';
                            var incomingPath = (function() {
                                try {
                                    var p = new URL(incomingUrl, window.location.origin).pathname;
                                    return stripTrailingSlash(p) || '/';
                                } catch (e) {
                                    var a = document.createElement('a');
                                    a.href = incomingUrl;
                                    return stripTrailingSlash(a.pathname) || '/';
                                }
                            })();
                            var ourPath = stripTrailingSlash(window.location.pathname) || '/';
                            if (incomingPath !== ourPath) return;
                        
                            const parser = new DOMParser();
                            const newDoc = parser.parseFromString(message.data.html, 'text/html');
                            document.documentElement.innerHTML = newDoc.documentElement.innerHTML;
                        
                            if (message.data.formState) {
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
                            }
                        
                            if (message.data.scrollState) {
                                window.scrollTo(message.data.scrollState.x, message.data.scrollState.y);
                            }
                        
                            if (message.data.activeElement) {
                                const ae = message.data.activeElement;
                                let element = null;
                                if (ae.id) {
                                    element = document.getElementById(ae.id);
                                } else if (ae.name) {
                                    element = document.querySelector(`[name="${ae.name}"]`);
                                }
                            
                                if (element) {
                                    if (ae.value !== null && element.value !== undefined) {
                                        element.value = ae.value;
                                    }
                                    if (ae.checked !== null && element.checked !== undefined) {
                                        element.checked = ae.checked;
                                    }
                                    if (element.tagName === 'SELECT' && ae.selectedIndex !== null) {
                                        element.selectedIndex = ae.selectedIndex;
                                    }
                                    setTimeout(function() {
                                        element.focus();
                                        if (element.tagName === 'SELECT' && ae.size !== null && ae.size > 1) {
                                            element.size = Math.min(ae.size, element.options.length);
                                            element.style.position = 'relative';
                                            element.style.zIndex = '9999';
                                        }
                                    }, 10);
                                }
                            }
                        
                            setTimeout(function() {
                                enforceAspectRatio();
                            }, 100);
                        }
                    }
                };
            
                ws.onopen = function() {
                    console.log('Browser connected to mirroring server (layout configurator)');
                    sendBrowserState();
                
                    let updateScheduled = false;
                    const observer = new MutationObserver(function(mutations) {
                        if (!updateScheduled) {
                            updateScheduled = true;
                            requestAnimationFrame(function() {
                                sendBrowserState();
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
                    function scheduleUpdate() {
                        if (!interactionScheduled) {
                            interactionScheduled = true;
                            requestAnimationFrame(function() {
                                sendBrowserState();
                                interactionScheduled = false;
                            });
                        }
                    }
                
                    document.addEventListener('click', scheduleUpdate, true);
                    document.addEventListener('input', scheduleUpdate, true);
                    document.addEventListener('change', scheduleUpdate, true);
                    document.addEventListener('focus', scheduleUpdate, true);
                    document.addEventListener('mousedown', scheduleUpdate, true);
                    document.addEventListener('mouseup', scheduleUpdate, true);
                    document.addEventListener('keydown', scheduleUpdate, true);
                    document.addEventListener('keyup', scheduleUpdate, true);
                };
            }
        
            // Keyboard shortcut: M opens menu
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

            (function() {
                var overlay = document.getElementById('glancerf-menu-overlay');
                if (overlay) overlay.addEventListener('click', function() {
                    var menu = document.getElementById('glancerf-menu');
                    if (menu) menu.classList.remove('open');
                });
            })();
})();