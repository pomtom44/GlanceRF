/* Conflict resolution for duplicate module settings. Used by layout and map-modules pages. */

(function () {
  'use strict';

  function getConflicts() {
    var cfg = window.LAYOUT_CONFIG || window.MAP_MODULES_CONFIG || {};
    return Array.isArray(cfg.conflicts) ? cfg.conflicts : [];
  }

  function renderConflictBanner(containerId) {
    var conflicts = getConflicts();
    var container = document.getElementById(containerId);
    if (!container) return;
    container.innerHTML = '';
    if (conflicts.length === 0) return;

    var wrap = document.createElement('div');
    wrap.className = 'conflict-resolution-banner';
    wrap.style.cssText = 'background:#3d1a0a;border:1px solid #8b4513;border-radius:6px;padding:12px 16px;margin-bottom:16px;color:#f0e0d0;';
    var title = document.createElement('div');
    title.style.cssText = 'font-weight:bold;margin-bottom:8px;';
    title.textContent = 'Conflicting settings detected';
    wrap.appendChild(title);
    var desc = document.createElement('div');
    desc.style.cssText = 'font-size:13px;margin-bottom:12px;color:#d0c0b0;';
    desc.textContent = 'The same module appears in multiple places with different settings. Choose one value to apply to all instances.';
    wrap.appendChild(desc);

    conflicts.forEach(function (c, idx) {
      var block = document.createElement('div');
      block.style.cssText = 'margin:12px 0;padding:10px;background:rgba(0,0,0,0.2);border-radius:4px;';
      var modLabel = (c.module_name || c.module_id) + ' – ' + (c.setting_label || c.setting_id);
      block.innerHTML = '<div style="font-weight:600;margin-bottom:6px;">' + escapeHtml(modLabel) + '</div>';
      var btnWrap = document.createElement('div');
      btnWrap.style.cssText = 'display:flex;flex-wrap:wrap;gap:8px;';
      (c.options || []).forEach(function (opt) {
        var btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'conflict-resolve-btn';
        btn.style.cssText = 'padding:6px 12px;background:#555;border:1px solid #777;color:#fff;border-radius:4px;cursor:pointer;font-size:12px;';
        btn.textContent = 'Use ' + (opt.label || opt.value || '');
        btn.dataset.moduleId = c.module_id;
        btn.dataset.settingId = c.setting_id;
        btn.dataset.value = opt.value;
        btn.dataset.conflictIdx = String(idx);
        btn.addEventListener('click', onResolveClick);
        btnWrap.appendChild(btn);
      });
      block.appendChild(btnWrap);
      wrap.appendChild(block);
    });
    container.appendChild(wrap);
  }

  function escapeHtml(s) {
    if (!s) return '';
    var div = document.createElement('div');
    div.textContent = s;
    return div.innerHTML;
  }

  function onResolveClick(ev) {
    var btn = ev.target;
    var moduleId = btn.dataset.moduleId;
    var settingId = btn.dataset.settingId;
    var value = btn.dataset.value;
    if (!moduleId || !settingId) return;
    btn.disabled = true;
    btn.textContent = 'Applying…';
    fetch('/api/config/resolve-module-conflict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ module_id: moduleId, setting_id: settingId, value: value })
    })
      .then(function (r) {
        if (!r.ok) return r.json().then(function (d) { throw new Error(d.error || 'Failed'); });
        return r.json();
      })
      .then(function () {
        window.location.reload();
      })
      .catch(function (err) {
        btn.disabled = false;
        btn.textContent = 'Use ' + (btn.dataset.value || '');
        alert('Failed to apply: ' + (err.message || err));
      });
  }

  window.renderConflictBanner = renderConflictBanner;
  window.getModuleConflicts = getConflicts;
})();
