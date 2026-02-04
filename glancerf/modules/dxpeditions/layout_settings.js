(function() {
    var TYPE = 'source_checkboxes';
    var SOURCES = [
        { id: 'NG3K', label: 'NG3K ADXO (plain)' },
        { id: 'NG3K RSS', label: 'NG3K RSS' },
        { id: 'DXCAL', label: 'DXCAL (danplanet.com)' }
    ];

    function updateHiddenFromCheckboxes(ui, hidden) {
        var checked = ui.querySelectorAll('input[type="checkbox"]:checked');
        var ids = [];
        checked.forEach(function(c) { ids.push(c.value); });
        hidden.value = JSON.stringify(ids);
    }

    function fillOne(container) {
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
        grid.style.gridTemplateColumns = 'repeat(auto-fill, minmax(180px, 1fr))';
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

    function run() {
        document.querySelectorAll('.cell-setting-custom[data-setting-type="' + TYPE + '"]').forEach(fillOne);
    }

    run();
    document.addEventListener('glancerf-cell-settings-updated', function() { run(); });
})();
