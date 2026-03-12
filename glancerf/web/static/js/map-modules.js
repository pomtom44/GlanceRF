/* Map only modules - 1xN grid, add/remove rows on change, module settings like layout editor */

(function () {
  'use strict';

  var cfg = window.MAP_MODULES_CONFIG || {};
  var MODULE_SETTINGS_BY_CELL = cfg.module_settings_by_cell || {};
  var MODULES_SETTINGS_SCHEMA = cfg.modules_settings_schema || {};
  window.GLANCERF_SETUP_CALLSIGN = cfg.setup_callsign != null ? cfg.setup_callsign : '';
  window.GLANCERF_SETUP_LOCATION = cfg.setup_location != null ? cfg.setup_location : '';

  var MODULE_OPTIONS = window.MAP_MODULE_OPTIONS || [];
  var grid = document.getElementById('map-modules-grid');
  var saveBtn = document.getElementById('map-modules-save');

  function getModuleColor(moduleId) {
    var mod = MODULE_OPTIONS.find(function (m) { return m.id === moduleId; });
    return (mod && mod.color) ? mod.color : '#111';
  }

  function buildOptionsHtml(selectedId) {
    var html = '<option value="">-- Add module --</option>';
    MODULE_OPTIONS.forEach(function (m) {
      var sel = m.id === selectedId ? ' selected' : '';
      html += '<option value="' + (m.id || '').replace(/"/g, '&quot;') + '"' + sel + '>' + (m.name || m.id || '').replace(/</g, '&lt;') + '</option>';
    });
    return html;
  }

  function updateCellSettings(cellEl) {
    var index = cellEl.getAttribute('data-index');
    var cellKey = 'map_overlay_' + index;
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
    var hasShowWhenSource = schema.some(function (x) { return x.show_when_source; });
    var lastBandCheckboxRow = null;
    var lastBandCheckboxId = null;
    var namePrefix = 'ms_' + cellKey;
    schema.forEach(function (s) {
      if (s.type === 'separator') {
        var sep = document.createElement('div');
        sep.className = 'cell-setting-separator';
        var line = document.createElement('div');
        line.className = 'cell-setting-separator-line';
        sep.appendChild(line);
        inner.appendChild(sep);
        return;
      }
      var cur = vals[s.id] !== undefined ? vals[s.id] : (s.default !== undefined ? s.default : '');
      if (!cur || cur === '') {
        if (s.id === 'callsign' && window.GLANCERF_SETUP_CALLSIGN) cur = window.GLANCERF_SETUP_CALLSIGN;
        else if ((s.id === 'location' || s.id === 'pass_location' || s.id === 'grid') && window.GLANCERF_SETUP_LOCATION) cur = window.GLANCERF_SETUP_LOCATION;
      }
      var rowWrap = null;
      if (hasShowWhenSource && s.show_when_source) {
        rowWrap = document.createElement('div');
        rowWrap.className = 'cell-setting-row';
        rowWrap.setAttribute('data-show-when-source', s.show_when_source);
      }
      var label = document.createElement('label');
      label.className = 'cell-setting-label';
      label.textContent = s.label;
      if (rowWrap) rowWrap.appendChild(label); else if (s.type !== 'checkbox' && s.type !== 'color') inner.appendChild(label);
      if (s.type === 'select') {
        var opts = s.options || [];
        if (s.optionsBySource && s.parentSettingId) {
          var parentVal = vals[s.parentSettingId];
          if (parentVal === undefined || parentVal === '' || !s.optionsBySource[parentVal]) parentVal = Object.keys(s.optionsBySource)[0];
          opts = s.optionsBySource[parentVal] || opts;
          var curInOpts = opts.some(function (opt) { return String(opt.value) === String(cur); });
          if (!curInOpts && opts.length && opts[0].value !== undefined) cur = opts[0].value;
        }
        var sel = document.createElement('select');
        sel.className = 'cell-setting-select';
        sel.setAttribute('name', namePrefix + '__' + s.id);
        if (s.optionsBySource && s.parentSettingId) {
          sel.setAttribute('data-parent-setting-id', s.parentSettingId);
          sel.setAttribute('data-options-by-source', JSON.stringify(s.optionsBySource));
        }
        opts.forEach(function (opt) {
          var op = document.createElement('option');
          op.value = opt.value;
          op.textContent = opt.label;
          if (String(opt.value) === String(cur)) op.selected = true;
          sel.appendChild(op);
        });
        if (rowWrap) { rowWrap.appendChild(sel); inner.appendChild(rowWrap); } else inner.appendChild(sel);
      } else if (s.type === 'number' || s.type === 'text') {
        var inp = document.createElement('input');
        inp.type = s.type;
        inp.className = 'cell-setting-select';
        inp.setAttribute('name', namePrefix + '__' + s.id);
        inp.value = cur;
        if (s.placeholder) inp.placeholder = s.placeholder;
        if (s.type === 'number') {
          if (s.min !== undefined) inp.min = s.min;
          if (s.max !== undefined) inp.max = s.max;
        }
        if (rowWrap) { rowWrap.appendChild(inp); inner.appendChild(rowWrap); } else inner.appendChild(inp);
      } else if (s.type === 'range') {
        var wrap = document.createElement('div');
        wrap.className = 'cell-setting-range-wrap';
        wrap.style.display = 'flex';
        wrap.style.alignItems = 'center';
        wrap.style.gap = '8px';
        var inp = document.createElement('input');
        inp.type = 'range';
        inp.className = 'cell-setting-select';
        inp.setAttribute('name', namePrefix + '__' + s.id);
        if (s.min !== undefined) inp.min = s.min;
        if (s.max !== undefined) inp.max = s.max;
        if (s.step !== undefined) inp.step = s.step;
        var numCur = (cur !== '' && cur !== undefined && cur !== null) ? Number(cur) : NaN;
        if (!isNaN(numCur) && s.min !== undefined && s.max !== undefined) numCur = Math.max(s.min, Math.min(s.max, numCur));
        inp.value = (!isNaN(numCur) ? numCur : (s.default !== undefined ? s.default : s.min !== undefined ? s.min : 0));
        var valSpan = document.createElement('span');
        valSpan.style.minWidth = '2.5em';
        valSpan.textContent = inp.value + (s.unit || '');
        inp.addEventListener('input', function () { valSpan.textContent = inp.value + (s.unit || ''); });
        wrap.appendChild(inp);
        wrap.appendChild(valSpan);
        if (rowWrap) { rowWrap.appendChild(wrap); inner.appendChild(rowWrap); } else inner.appendChild(wrap);
      } else if (s.type === 'checkbox') {
        var inp = document.createElement('input');
        inp.type = 'checkbox';
        inp.className = 'cell-setting-select';
        inp.setAttribute('name', namePrefix + '__' + s.id);
        inp.checked = (cur === true || cur === 'true' || cur === 1 || cur === '1');
        var rowEl = document.createElement('div');
        rowEl.className = 'cell-setting-row cell-setting-inline-row';
        rowEl.style.display = 'flex';
        rowEl.style.alignItems = 'center';
        rowEl.style.gap = '8px';
        rowEl.appendChild(label);
        rowEl.appendChild(inp);
        inner.appendChild(rowEl);
        if (s.id && s.id.indexOf('band_') === 0 && s.id.indexOf('_color') === -1) {
          lastBandCheckboxRow = rowEl;
          lastBandCheckboxId = s.id;
        } else {
          lastBandCheckboxRow = null;
          lastBandCheckboxId = null;
        }
      } else if (s.type === 'color') {
        var hex = (cur && /^#[0-9A-Fa-f]{3,8}$/.test(String(cur))) ? String(cur) : (s.default && /^#[0-9A-Fa-f]{3,8}$/.test(String(s.default)) ? String(s.default) : '#0f0');
        var inp = document.createElement('input');
        inp.type = 'color';
        inp.className = 'cell-setting-select';
        inp.setAttribute('name', namePrefix + '__' + s.id);
        inp.value = hex;
        if (lastBandCheckboxRow && lastBandCheckboxId && s.id === lastBandCheckboxId + '_color') {
          lastBandCheckboxRow.classList.add('cell-setting-band-row');
          var spacer = document.createElement('span');
          spacer.className = 'cell-setting-inline-spacer';
          var colorLabel = document.createElement('span');
          colorLabel.className = 'cell-setting-label cell-setting-color-label';
          colorLabel.textContent = s.label;
          lastBandCheckboxRow.appendChild(spacer);
          lastBandCheckboxRow.appendChild(colorLabel);
          lastBandCheckboxRow.appendChild(inp);
          lastBandCheckboxRow = null;
          lastBandCheckboxId = null;
        } else {
          var rowEl = document.createElement('div');
          rowEl.className = 'cell-setting-row cell-setting-inline-row';
          rowEl.style.display = 'flex';
          rowEl.style.alignItems = 'center';
          rowEl.style.gap = '8px';
          rowEl.appendChild(label);
          rowEl.appendChild(inp);
          inner.appendChild(rowEl);
        }
      } else {
        var customWrap = document.createElement('div');
        customWrap.className = 'cell-setting-custom';
        customWrap.setAttribute('data-setting-type', s.type);
        customWrap.setAttribute('data-cell-key', cellKey);
        customWrap.setAttribute('data-setting-id', s.id);
        customWrap.setAttribute('data-current-value', typeof cur === 'string' ? cur : (cur != null ? JSON.stringify(cur) : ''));
        var hidden = document.createElement('input');
        hidden.type = 'hidden';
        hidden.className = 'cell-setting-custom-value';
        hidden.setAttribute('name', namePrefix + '__' + s.id);
        hidden.value = typeof cur === 'string' ? cur : (cur != null ? JSON.stringify(cur) : '');
        var customUi = document.createElement('div');
        customUi.className = 'cell-setting-custom-ui';
        customWrap.appendChild(hidden);
        customWrap.appendChild(customUi);
        if (rowWrap) { rowWrap.appendChild(customWrap); inner.appendChild(rowWrap); } else inner.appendChild(customWrap);
      }
      if (s.hintUrl) {
        var hintLink = document.createElement('a');
        hintLink.href = s.hintUrl;
        hintLink.target = '_blank';
        hintLink.rel = 'noopener noreferrer';
        hintLink.textContent = s.hintText || 'Guide';
        hintLink.className = 'cell-setting-hint-link';
        inner.appendChild(hintLink);
      }
    });
    container.appendChild(inner);
    if (hasShowWhenSource) {
      var sourceSelect = container.querySelector('select[name="' + namePrefix + '__source_type"]');
      if (sourceSelect) {
        function applyWebcamSourceVisibility() {
          var v = sourceSelect.value;
          container.querySelectorAll('.cell-setting-row[data-show-when-source]').forEach(function (rowEl) {
            rowEl.style.display = (rowEl.getAttribute('data-show-when-source') === v) ? '' : 'none';
          });
        }
        applyWebcamSourceVisibility();
        sourceSelect.addEventListener('change', applyWebcamSourceVisibility);
      }
    }
    try {
      document.dispatchEvent(new CustomEvent('glancerf-cell-settings-updated', { detail: { container: container } }));
    } catch (e) {}
  }

  function updateAllCellSettings() {
    if (!grid) return;
    grid.querySelectorAll('.map-module-cell').forEach(updateCellSettings);
  }

  function buildCellHtml(index, moduleId) {
    var color = getModuleColor(moduleId);
    var opts = buildOptionsHtml(moduleId);
    var removeBtn = moduleId
      ? '<button type="button" class="map-module-remove" data-index="' + index + '" title="Remove">×</button>'
      : '';
    return (
      '<div class="map-module-cell grid-cell" data-index="' + index + '" style="background-color:' + color + ';">' +
      '<select class="cell-widget-select map-module-select" data-index="' + index + '">' + opts + '</select>' +
      '<div class="cell-module-settings"></div>' +
      removeBtn +
      '</div>'
    );
  }

  function getModulesFromGrid() {
    var cells = grid.querySelectorAll('.map-module-cell');
    var list = [];
    for (var i = 0; i < cells.length; i++) {
      var sel = cells[i].querySelector('.map-module-select');
      var val = sel ? (sel.value || '').trim() : '';
      if (val) list.push(val);
    }
    return list;
  }

  function rebuildGrid(modulesList) {
    var rows = modulesList.concat(['']);
    var html = '';
    for (var i = 0; i < rows.length; i++) {
      html += buildCellHtml(i, rows[i]);
    }
    grid.innerHTML = html;
    attachCellListeners();
    updateAllCellSettings();
  }

  function attachCellListeners() {
    grid.querySelectorAll('.map-module-select').forEach(function (sel) {
      sel.addEventListener('change', function () {
        var idx = parseInt(sel.getAttribute('data-index'), 10);
        var val = (sel.value || '').trim();
        var cell = sel.closest('.map-module-cell');
        if (cell) cell.style.backgroundColor = getModuleColor(val);
        updateCellSettings(cell);

        var modules = getModulesFromGrid();
        var isLast = idx === grid.querySelectorAll('.map-module-cell').length - 1;
        if ((isLast && val) || (!isLast && !val)) {
          rebuildGrid(modules);
        }
      });
    });

    grid.querySelectorAll('.map-module-remove').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var idx = parseInt(btn.getAttribute('data-index'), 10);
        var modules = getModulesFromGrid();
        if (idx < modules.length) {
          modules.splice(idx, 1);
          rebuildGrid(modules);
        }
      });
    });
  }

  function collectModuleSettings() {
    var module_settings = {};
    document.querySelectorAll('#map-modules-grid [name^="ms_map_overlay_"]').forEach(function (el) {
      var name = el.getAttribute('name');
      if (!name || name.indexOf('__') === -1) return;
      var i = name.indexOf('__');
      var cellPart = name.slice(3, i);
      var settingId = name.slice(i + 2);
      if (cellPart && settingId) {
        if (!module_settings[cellPart]) module_settings[cellPart] = {};
        if (el.type === 'checkbox') {
          module_settings[cellPart][settingId] = el.checked;
        } else {
          module_settings[cellPart][settingId] = el.value || '';
        }
      }
    });
    return module_settings;
  }

  function doSave() {
    var modules = getModulesFromGrid();
    var module_settings = collectModuleSettings();
    saveBtn.disabled = true;
    saveBtn.textContent = 'Saving...';
    fetch('/api/map-modules', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ modules: modules, module_settings: module_settings }),
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data.success) {
          window.location.href = '/';
        } else {
          alert(data.error || 'Save failed');
          saveBtn.disabled = false;
          saveBtn.textContent = 'Save & back to dashboard';
        }
      })
      .catch(function () {
        alert('Save request failed');
        saveBtn.disabled = false;
        saveBtn.textContent = 'Save & back to dashboard';
      });
  }

  document.addEventListener('change', function (e) {
    if (e.target && e.target.classList && e.target.classList.contains('cell-widget-select')) {
      var cell = e.target.closest('.map-module-cell');
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
      var curInOpts = opts.some(function (opt) { return String(opt.value) === String(cur); });
      if (!curInOpts) cur = opts[0].value;
      dependent.innerHTML = '';
      opts.forEach(function (opt) {
        var op = document.createElement('option');
        op.value = opt.value;
        op.textContent = opt.label;
        if (String(opt.value) === String(cur)) op.selected = true;
        dependent.appendChild(op);
      });
      dependent.value = cur;
    }
  });

  document.addEventListener('DOMContentLoaded', function () {
    attachCellListeners();
    updateAllCellSettings();
    setTimeout(updateAllCellSettings, 100);
    if (saveBtn) saveBtn.addEventListener('click', doSave);
    if (typeof window.renderConflictBanner === 'function') {
      window.renderConflictBanner('conflict-resolution-container');
    }
  });
})();
