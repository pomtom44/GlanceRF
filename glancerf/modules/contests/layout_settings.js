(function() {
    var TYPE_SOURCES = 'source_checkboxes';
    var TYPE_CUSTOM = 'custom_sources';
    var SOURCES = [
        { id: 'WA7BNM', label: 'WA7BNM Contest Calendar (RSS)' },
        { id: 'WA7BNM iCal', label: 'WA7BNM iCal' },
        { id: 'SSA (SE)', label: 'SSA Sweden (RSS)' },
        { id: 'SSA (SE) iCal', label: 'SSA Sweden (iCal)' },
        { id: 'RSGB (UK)', label: 'RSGB UK HF' }
    ];

    function updateHiddenFromCheckboxes(ui, hidden) {
        var checked = ui.querySelectorAll('input[type="checkbox"]:checked');
        var ids = [];
        checked.forEach(function(c) { ids.push(c.value); });
        hidden.value = JSON.stringify(ids);
    }

    function fillOneSourceCheckboxes(container) {
        var ui = container.querySelector('.cell-setting-custom-ui');
        var hidden = container.querySelector('.cell-setting-custom-value');
        if (!ui || !hidden || ui.getAttribute('data-filled') === '1') return;
        ui.setAttribute('data-filled', '1');
        ui.style.border = '1px solid #333';
        ui.style.borderRadius = '3px';
        ui.style.padding = '6px';
        ui.style.background = '#000';
        ui.style.fontSize = '12px';

        var currentValue = container.getAttribute('data-current-value') || '';
        var selectedIds = [];
        try {
            if (currentValue.trim()) selectedIds = JSON.parse(currentValue);
            if (!Array.isArray(selectedIds)) selectedIds = [];
        } catch (e) { selectedIds = []; }

        var toolbar = document.createElement('div');
        toolbar.style.marginBottom = '8px';
        toolbar.style.display = 'flex';
        toolbar.style.gap = '8px';
        var selectAllBtn = document.createElement('button');
        selectAllBtn.type = 'button';
        selectAllBtn.textContent = 'Select all';
        selectAllBtn.style.fontSize = '12px';
        selectAllBtn.style.padding = '4px 8px';
        selectAllBtn.style.cursor = 'pointer';
        selectAllBtn.style.background = '#333';
        selectAllBtn.style.color = '#fff';
        selectAllBtn.style.border = '1px solid #555';
        selectAllBtn.style.borderRadius = '3px';
        var selectNoneBtn = document.createElement('button');
        selectNoneBtn.type = 'button';
        selectNoneBtn.textContent = 'Select none';
        selectNoneBtn.style.fontSize = '12px';
        selectNoneBtn.style.padding = '4px 8px';
        selectNoneBtn.style.cursor = 'pointer';
        selectNoneBtn.style.background = '#333';
        selectNoneBtn.style.color = '#fff';
        selectNoneBtn.style.border = '1px solid #555';
        selectNoneBtn.style.borderRadius = '3px';
        toolbar.appendChild(selectAllBtn);
        toolbar.appendChild(selectNoneBtn);
        ui.appendChild(toolbar);

        var grid = document.createElement('div');
        grid.style.display = 'grid';
        grid.style.gridTemplateColumns = 'repeat(auto-fill, minmax(200px, 1fr))';
        grid.style.gap = '4px 12px';
        grid.style.alignContent = 'start';
        SOURCES.forEach(function(src) {
            var lab = document.createElement('label');
            lab.style.display = 'block';
            lab.style.cursor = 'pointer';
            lab.style.whiteSpace = 'nowrap';
            lab.style.overflow = 'hidden';
            lab.style.textOverflow = 'ellipsis';
            var cb = document.createElement('input');
            cb.type = 'checkbox';
            cb.value = src.id;
            cb.checked = selectedIds.indexOf(src.id) >= 0;
            cb.addEventListener('change', function() { updateHiddenFromCheckboxes(ui, hidden); });
            lab.appendChild(cb);
            lab.appendChild(document.createTextNode(' ' + src.label));
            grid.appendChild(lab);
        });
        ui.appendChild(grid);
        selectAllBtn.addEventListener('click', function() {
            grid.querySelectorAll('input[type="checkbox"]').forEach(function(c) { c.checked = true; });
            updateHiddenFromCheckboxes(ui, hidden);
        });
        selectNoneBtn.addEventListener('click', function() {
            grid.querySelectorAll('input[type="checkbox"]').forEach(function(c) { c.checked = false; });
            updateHiddenFromCheckboxes(ui, hidden);
        });
    }

    function updateCustomSourcesHidden(container) {
        var ui = container.querySelector('.cell-setting-custom-ui');
        var hidden = container.querySelector('.cell-setting-custom-value');
        if (!ui || !hidden) return;
        var rows = ui.querySelectorAll('.custom-source-row');
        var arr = [];
        rows.forEach(function(row) {
            var urlInp = row.querySelector('.custom-source-url');
            var typeSel = row.querySelector('.custom-source-type');
            var labelInp = row.querySelector('.custom-source-label');
            var url = (urlInp && urlInp.value) ? urlInp.value.trim() : '';
            if (!url) return;
            arr.push({
                url: url,
                type: (typeSel && typeSel.value) ? typeSel.value : 'rss',
                label: (labelInp && labelInp.value) ? labelInp.value.trim() : ''
            });
        });
        hidden.value = JSON.stringify(arr);
    }

    function fillOneCustomSources(container) {
        var ui = container.querySelector('.cell-setting-custom-ui');
        var hidden = container.querySelector('.cell-setting-custom-value');
        if (!ui || !hidden || ui.getAttribute('data-filled') === '1') return;
        ui.setAttribute('data-filled', '1');
        ui.style.border = '1px solid #333';
        ui.style.borderRadius = '3px';
        ui.style.padding = '6px';
        ui.style.background = '#000';
        ui.style.fontSize = '12px';

        var currentValue = container.getAttribute('data-current-value') || '';
        var list = [];
        try {
            if (currentValue.trim()) list = JSON.parse(currentValue);
            if (!Array.isArray(list)) list = [];
        } catch (e) { list = []; }

        function addRow(data) {
            data = data || { url: '', type: 'rss', label: '' };
            var row = document.createElement('div');
            row.className = 'custom-source-row';
            row.style.display = 'grid';
            row.style.gridTemplateColumns = '1fr auto 120px 28px';
            row.style.gap = '6px';
            row.style.marginBottom = '6px';
            row.style.alignItems = 'center';
            var urlInp = document.createElement('input');
            urlInp.type = 'url';
            urlInp.placeholder = 'https://... (RSS or iCal)';
            urlInp.className = 'custom-source-url';
            urlInp.value = data.url || '';
            urlInp.style.width = '100%';
            urlInp.style.fontSize = '12px';
            urlInp.style.padding = '4px';
            var typeSel = document.createElement('select');
            typeSel.className = 'custom-source-type';
            typeSel.style.fontSize = '12px';
            typeSel.style.padding = '4px';
            ['rss', 'ical'].forEach(function(opt) {
                var o = document.createElement('option');
                o.value = opt;
                o.textContent = opt.toUpperCase();
                if ((data.type || 'rss').toLowerCase() === opt) o.selected = true;
                typeSel.appendChild(o);
            });
            var labelInp = document.createElement('input');
            labelInp.type = 'text';
            labelInp.placeholder = 'Label (optional)';
            labelInp.className = 'custom-source-label';
            labelInp.value = data.label || '';
            labelInp.style.fontSize = '12px';
            labelInp.style.padding = '4px';
            var removeBtn = document.createElement('button');
            removeBtn.type = 'button';
            removeBtn.textContent = 'X';
            removeBtn.style.fontSize = '11px';
            removeBtn.style.padding = '2px 6px';
            removeBtn.style.cursor = 'pointer';
            removeBtn.style.background = '#333';
            removeBtn.style.color = '#fff';
            removeBtn.style.border = '1px solid #555';
            removeBtn.style.borderRadius = '3px';
            function sync() { updateCustomSourcesHidden(container); }
            urlInp.addEventListener('input', sync);
            typeSel.addEventListener('change', sync);
            labelInp.addEventListener('input', sync);
            removeBtn.addEventListener('click', function() {
                row.remove();
                sync();
            });
            row.appendChild(urlInp);
            row.appendChild(typeSel);
            row.appendChild(labelInp);
            row.appendChild(removeBtn);
            ui.appendChild(row);
        }

        list.forEach(function(item) {
            addRow(typeof item === 'object' && item ? item : { url: '', type: 'rss', label: '' });
        });
        if (list.length === 0) addRow({ url: '', type: 'rss', label: '' });

        var addBtn = document.createElement('button');
        addBtn.type = 'button';
        addBtn.textContent = 'Add source';
        addBtn.style.fontSize = '12px';
        addBtn.style.padding = '4px 8px';
        addBtn.style.marginTop = '4px';
        addBtn.style.cursor = 'pointer';
        addBtn.style.background = '#333';
        addBtn.style.color = '#fff';
        addBtn.style.border = '1px solid #555';
        addBtn.style.borderRadius = '3px';
        addBtn.addEventListener('click', function() {
            addRow({ url: '', type: 'rss', label: '' });
            updateCustomSourcesHidden(container);
        });
        ui.appendChild(addBtn);
    }

    function run() {
        document.querySelectorAll('.cell-setting-custom[data-setting-type="' + TYPE_SOURCES + '"]').forEach(fillOneSourceCheckboxes);
        document.querySelectorAll('.cell-setting-custom[data-setting-type="' + TYPE_CUSTOM + '"]').forEach(fillOneCustomSources);
    }

    run();
    document.addEventListener('glancerf-cell-settings-updated', function() { run(); });
})();
