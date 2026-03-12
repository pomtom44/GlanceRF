(function() {
    var SETTING_TYPE = 'satellite_table';
    var DEFAULT_COLOR_PALETTE = [
        '#e6194b', '#3cb44b', '#4363d8', '#f58231', '#911eb4', '#46f0f0',
        '#f032e6', '#bcf60c', '#fabebe', '#008080', '#e6beff', '#9a6324',
        '#fffac8', '#800000', '#aaffc3', '#808000', '#ffd8b1', '#000075'
    ];
    function defaultColorForNorad(noradStr) {
        var n = parseInt(noradStr, 10) || 0;
        var idx = Math.abs(n) % DEFAULT_COLOR_PALETTE.length;
        return DEFAULT_COLOR_PALETTE[idx];
    }
    function defaultSatEntry() {
        return { show_passes: true, show_on_map: true, show_traces: true, show_label: true, color: '' };
    }

    function fillSatelliteTable(container) {
        var wrap = container.querySelector('.cell-setting-custom[data-setting-type="' + SETTING_TYPE + '"]');
        if (!wrap || wrap.getAttribute('data-filled') === '1') return;
        var hidden = wrap.querySelector('.cell-setting-custom-value');
        var ui = wrap.querySelector('.cell-setting-custom-ui');
        if (!hidden || !ui) return;
        wrap.setAttribute('data-filled', '1');

        var cellKey = wrap.getAttribute('data-cell-key') || '';
        var currentRaw = (wrap.getAttribute('data-current-value') || '').trim();
        var state = {};
        try {
            if (currentRaw) state = JSON.parse(currentRaw);
            if (typeof state !== 'object' || state === null) state = {};
        } catch (e) {
            state = {};
        }

        ui.innerHTML = 'Loading...';
        ui.style.fontSize = '12px';

        fetch('/api/satellite/list').then(function(r) { return r.ok ? r.json() : { satellites: [] }; }).then(function(data) {
            var list = (data && data.satellites) ? data.satellites : [];
            ui.innerHTML = '';
            var styleEl = document.createElement('style');
            styleEl.textContent = '.sat-settings-table .sat-settings-toggle-btn { font-size: 11px; padding: 4px 10px; cursor: pointer; background-color: #1a1a1a; border: 1px solid #333; color: #ccc; border-radius: 4px; box-sizing: border-box; } .sat-settings-table .sat-settings-toggle-btn:hover { border-color: #0f0; color: #0f0; background-color: #222; } .sat-settings-table .sat-settings-toggle-btn:active { background-color: #252525; }';
            wrap.appendChild(styleEl);

            var table = document.createElement('table');
            table.className = 'sat-settings-table';
            table.style.width = '100%';
            table.style.borderCollapse = 'collapse';
            table.style.marginTop = '8px';
            table.style.fontSize = '12px';

            var thead = document.createElement('thead');
            var headerRow = document.createElement('tr');
            function addToggleBtn(th, label, checked) {
                var btn = document.createElement('button');
                btn.type = 'button';
                btn.className = 'sat-settings-toggle-btn';
                btn.textContent = label;
                btn.addEventListener('click', function() {
                    tbody.querySelectorAll('input[type="checkbox"][data-key]').forEach(function(cb) { cb.checked = !!checked; });
                    serialize();
                });
                th.appendChild(btn);
            }
            var thName = document.createElement('th');
            thName.style.textAlign = 'left';
            thName.style.padding = '4px 6px';
            thName.style.borderBottom = '1px solid #333';
            thName.style.verticalAlign = 'middle';
            var btnWrap = document.createElement('span');
            btnWrap.style.display = 'inline-flex';
            btnWrap.style.gap = '6px';
            btnWrap.style.alignItems = 'center';
            addToggleBtn(btnWrap, 'All on', true);
            addToggleBtn(btnWrap, 'All off', false);
            thName.appendChild(btnWrap);
            headerRow.appendChild(thName);
            ['Show Passes', 'Show On Map', 'Show Traces', 'Show Label', 'Color'].forEach(function(t) {
                var th = document.createElement('th');
                th.textContent = t;
                th.style.textAlign = 'left';
                th.style.padding = '4px 6px';
                th.style.borderBottom = '1px solid #333';
                headerRow.appendChild(th);
            });
            thead.appendChild(headerRow);
            table.appendChild(thead);

            var tbody = document.createElement('tbody');
            list.forEach(function(sat) {
                var norad = sat.norad_id != null ? String(sat.norad_id) : '';
                var name = (sat.name || 'NORAD ' + norad || '').trim();
                if (!norad) return;

                var entry = state[norad];
                if (!entry || typeof entry !== 'object') entry = defaultSatEntry();
                if (entry.show_passes === undefined) entry.show_passes = true;
                if (entry.show_on_map === undefined) entry.show_on_map = true;
                if (entry.show_traces === undefined) entry.show_traces = true;
                if (entry.show_label === undefined) entry.show_label = true;
                if (entry.color === undefined) entry.color = '';

                var tr = document.createElement('tr');
                tr.setAttribute('data-norad', norad);

                var tdName = document.createElement('td');
                tdName.textContent = name;
                tdName.style.padding = '4px 6px';
                tdName.style.borderBottom = '1px solid #ddd';
                tdName.style.maxWidth = '140px';
                tdName.style.overflow = 'hidden';
                tdName.style.textOverflow = 'ellipsis';
                tdName.style.whiteSpace = 'nowrap';
                tr.appendChild(tdName);

                function makeCb(key) {
                    var td = document.createElement('td');
                    td.style.padding = '4px 6px';
                    td.style.borderBottom = '1px solid #ddd';
                    var cb = document.createElement('input');
                    cb.type = 'checkbox';
                    cb.checked = !!entry[key];
                    cb.setAttribute('data-norad', norad);
                    cb.setAttribute('data-key', key);
                    td.appendChild(cb);
                    tr.appendChild(td);
                    return cb;
                }
                makeCb('show_passes');
                makeCb('show_on_map');
                makeCb('show_traces');
                makeCb('show_label');

                var tdColor = document.createElement('td');
                tdColor.style.padding = '4px 6px';
                tdColor.style.borderBottom = '1px solid #ddd';
                var colorInp = document.createElement('input');
                colorInp.type = 'color';
                colorInp.setAttribute('data-norad', norad);
                var hasExplicitColor = entry.color && /^#[0-9A-Fa-f]{6}$/.test(entry.color);
                colorInp.value = hasExplicitColor ? entry.color : defaultColorForNorad(norad);
                if (!hasExplicitColor) colorInp.setAttribute('data-default-color', '1');
                colorInp.style.width = '28px';
                colorInp.style.height = '22px';
                colorInp.style.padding = '0';
                colorInp.style.border = '1px solid #999';
                colorInp.addEventListener('input', function() { colorInp.removeAttribute('data-default-color'); });
                colorInp.addEventListener('change', function() { colorInp.removeAttribute('data-default-color'); });
                tdColor.appendChild(colorInp);
                tr.appendChild(tdColor);

                tbody.appendChild(tr);
            });

            table.appendChild(tbody);
            ui.appendChild(table);

            function serialize() {
                var out = {};
                tbody.querySelectorAll('tr[data-norad]').forEach(function(tr) {
                    var norad = tr.getAttribute('data-norad');
                    var cbs = tr.querySelectorAll('input[type="checkbox"][data-key]');
                    var colorInp = tr.querySelector('input[type="color"]');
                    var show_passes = true, show_on_map = true, show_traces = true, show_label = true;
                    cbs.forEach(function(cb) {
                        var k = cb.getAttribute('data-key');
                        if (k === 'show_passes') show_passes = cb.checked;
                        else if (k === 'show_on_map') show_on_map = cb.checked;
                        else if (k === 'show_traces') show_traces = cb.checked;
                        else if (k === 'show_label') show_label = cb.checked;
                    });
                    var color = '';
                    if (colorInp) {
                        if (colorInp.getAttribute('data-default-color') === '1') color = '';
                        else if (colorInp.value) color = colorInp.value;
                    }
                    out[norad] = { show_passes: show_passes, show_on_map: show_on_map, show_traces: show_traces, show_label: show_label, color: color };
                });
                hidden.value = JSON.stringify(out);
            }

            tbody.addEventListener('change', function(e) {
                if (e.target && (e.target.type === 'checkbox' || e.target.type === 'color') && e.target.closest('.sat-settings-table')) {
                    serialize();
                }
            });
            tbody.addEventListener('input', function(e) {
                if (e.target && e.target.type === 'color' && e.target.closest('.sat-settings-table')) {
                    serialize();
                }
            });

            serialize();
        }).catch(function() {
            ui.innerHTML = 'Could not load satellite list.';
        });
    }

    function run() {
        document.querySelectorAll('.cell-module-settings').forEach(function(container) {
            var parent = container.closest('.grid-cell') || container.closest('.map-module-cell');
            var select = parent && parent.querySelector('.cell-widget-select, .map-module-select');
            if (select && select.value === 'satellite_pass') {
                fillSatelliteTable(container);
            }
        });
    }

    run();
    document.addEventListener('glancerf-cell-settings-updated', function() {
        document.querySelectorAll('.cell-setting-custom[data-setting-type="' + SETTING_TYPE + '"]').forEach(function(wrap) {
            wrap.removeAttribute('data-filled');
        });
        run();
    });
})();
