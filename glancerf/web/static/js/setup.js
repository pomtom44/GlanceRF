(function () {
  'use strict';

  var cfg = window.SETUP_CONFIG || {};
  var currentAspectRatio = cfg.current_ratio != null ? cfg.current_ratio : '16:9';
  var currentOrientation = cfg.current_orientation != null ? cfg.current_orientation : 'landscape';
  var targetRatio = 16 / 9;

  function getDOMElements() {
    return {
      gridColumnsInput: document.getElementById('grid_columns'),
      gridRowsInput: document.getElementById('grid_rows'),
      aspectRatioSelect: document.getElementById('aspect_ratio'),
      orientationSelect: document.getElementById('orientation'),
      columnsValue: document.getElementById('columns-value'),
      rowsValue: document.getElementById('rows-value'),
      previewSquare: document.getElementById('preview-square'),
      previewContainer: document.getElementById('preview-square') && document.getElementById('preview-square').parentElement,
      sliderContainerInner: document.querySelector('.slider-container-inner'),
      previewWrapper: document.querySelector('.preview-wrapper'),
      rowSliderWrapper: document.querySelector('.slider-vertical-wrapper'),
      sliderRotated: document.querySelector('.slider-vertical-rotated')
    };
  }

  function updateBoxDimensions() {
    var els = getDOMElements();
    if (!els.previewContainer || !els.previewSquare) return;
    var orientation = (els.orientationSelect && els.orientationSelect.value) || currentOrientation;
    var isPortrait = orientation === 'portrait';
    var containerWidth = els.previewContainer.offsetWidth;
    var maxHeightPx = Math.min(window.innerHeight * 0.55, 500);
    var boxWidth, boxHeight;
    if (isPortrait) {
      var displayRatio = 1 / targetRatio;
      boxHeight = maxHeightPx;
      boxWidth = boxHeight * displayRatio;
    } else {
      if (containerWidth <= 0) return;
      displayRatio = targetRatio;
      boxWidth = containerWidth;
      boxHeight = containerWidth / displayRatio;
    }
    els.previewSquare.style.width = boxWidth + 'px';
    els.previewSquare.style.height = boxHeight + 'px';
    if (els.previewContainer) {
      if (isPortrait) {
        els.previewContainer.style.width = boxWidth + 'px';
        els.previewContainer.style.maxWidth = boxWidth + 'px';
      } else {
        els.previewContainer.style.width = '';
        els.previewContainer.style.maxWidth = '';
      }
    }
    if (els.sliderContainerInner && els.previewWrapper) {
      els.sliderContainerInner.style.width = boxWidth + 'px';
      var wrapperRect = els.previewWrapper.getBoundingClientRect();
      var boxRect = els.previewSquare.getBoundingClientRect();
      var rightEdge = boxRect.right - wrapperRect.left;
      els.sliderContainerInner.style.marginRight = (els.previewWrapper.offsetWidth - rightEdge) + 'px';
    }
    if (els.rowSliderWrapper && boxHeight > 0) {
      els.rowSliderWrapper.style.height = boxHeight + 'px';
      if (els.sliderRotated) {
        els.sliderRotated.style.width = boxHeight + 'px';
        els.sliderRotated.style.height = '8px';
        els.sliderRotated.style.marginLeft = (-boxHeight / 2) + 'px';
      }
    }
  }

  function updatePreview() {
    var els = getDOMElements();
    if (!els.gridColumnsInput || !els.gridRowsInput || !els.aspectRatioSelect ||
        !els.columnsValue || !els.rowsValue || !els.previewSquare) {
      return;
    }
    var columns = parseInt(els.gridColumnsInput.value, 10);
    var rows = parseInt(els.gridRowsInput.value, 10);
    var aspectRatio = els.aspectRatioSelect.value;
    if (els.orientationSelect) currentOrientation = els.orientationSelect.value;
    els.columnsValue.textContent = columns;
    els.rowsValue.textContent = rows;
    currentAspectRatio = aspectRatio;
    var ratioParts = aspectRatio.split(':');
    targetRatio = parseFloat(ratioParts[0]) / parseFloat(ratioParts[1]);
    els.previewSquare.style.gridTemplateColumns = 'repeat(' + columns + ', 1fr)';
    els.previewSquare.style.gridTemplateRows = 'repeat(' + rows + ', 1fr)';
    var fragment = document.createDocumentFragment();
    for (var i = 0; i < columns * rows; i++) {
      var cell = document.createElement('div');
      cell.className = 'preview-cell';
      fragment.appendChild(cell);
    }
    els.previewSquare.innerHTML = '';
    els.previewSquare.appendChild(fragment);
    requestAnimationFrame(function () {
      updateBoxDimensions();
      setTimeout(updateBoxDimensions, 50);
    });
  }

  function initializeEventListeners() {
    var els = getDOMElements();
    if (!els.gridColumnsInput || !els.gridRowsInput || !els.aspectRatioSelect) return;
    els.gridColumnsInput.addEventListener('input', updatePreview);
    els.gridRowsInput.addEventListener('input', updatePreview);
    els.aspectRatioSelect.addEventListener('change', updatePreview);
    if (els.orientationSelect) {
      els.orientationSelect.addEventListener('change', updatePreview);
    }
  }

  var resizeTimeout;
  window.addEventListener('resize', function () {
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(updatePreview, 100);
  });

  function showSetupPage(num) {
    var page1 = document.getElementById('setup-page-1');
    var page2 = document.getElementById('setup-page-2');
    var page3 = document.getElementById('setup-page-3');
    var page4 = document.getElementById('setup-page-4');
    var tab1 = document.getElementById('tab-page-1');
    var tab2 = document.getElementById('tab-page-2');
    var tab3 = document.getElementById('tab-page-3');
    var tab4 = document.getElementById('tab-page-4');
    if (page1) page1.classList.toggle('active', num === 1);
    if (page2) page2.classList.toggle('active', num === 2);
    if (page3) page3.classList.toggle('active', num === 3);
    if (page4) page4.classList.toggle('active', num === 4);
    if (tab1) tab1.classList.toggle('active', num === 1);
    if (tab2) tab2.classList.toggle('active', num === 2);
    if (tab3) tab3.classList.toggle('active', num === 3);
    if (tab4) tab4.classList.toggle('active', num === 4);
    if (num === 1 && window._gpsLoadOnShow) window._gpsLoadOnShow();
    if (num === 3) { updatePreview(); setTimeout(updatePreview, 100); }
  }

  var nextBtn = document.getElementById('setup-next-btn');
  var nextBtn2 = document.getElementById('setup-next-btn-2');
  var nextBtn3 = document.getElementById('setup-next-btn-3');
  var backBtn = document.getElementById('setup-back-btn');
  var backBtn3 = document.getElementById('setup-back-btn-3');
  var backBtn4 = document.getElementById('setup-back-btn-4');
  var tab1 = document.getElementById('tab-page-1');
  var tab2 = document.getElementById('tab-page-2');
  var tab3 = document.getElementById('tab-page-3');
  var tab4 = document.getElementById('tab-page-4');
  if (nextBtn) nextBtn.addEventListener('click', function () { showSetupPage(2); });
  if (nextBtn2) nextBtn2.addEventListener('click', function () { showSetupPage(3); });
  if (nextBtn3) nextBtn3.addEventListener('click', function () { showSetupPage(4); });
  if (backBtn) backBtn.addEventListener('click', function () { showSetupPage(1); });
  if (backBtn3) backBtn3.addEventListener('click', function () { showSetupPage(2); });
  if (backBtn4) backBtn4.addEventListener('click', function () { showSetupPage(3); });
  if (tab1) tab1.addEventListener('click', function () { showSetupPage(1); });
  if (tab2) tab2.addEventListener('click', function () { showSetupPage(2); });
  if (tab3) tab3.addEventListener('click', function () { showSetupPage(3); });
  if (tab4) tab4.addEventListener('click', function () { showSetupPage(4); });

  function initGpsTab() {
    var container = document.getElementById('gps-status-container');
    var gpsSection = document.getElementById('gps-section');
    var gpsNoConnect = document.getElementById('gps-no-connect-msg');
    var refreshBtn = document.getElementById('gps-refresh-btn');
    var refreshNoConnectBtn = document.getElementById('gps-refresh-no-connect-btn');
    var sourceSelect = document.getElementById('gps_source');
    var portRow = document.getElementById('gps-serial-port-row');
    var portSelect = document.getElementById('gps_serial_port');
    var locationToggle = document.getElementById('gps_location_enabled');
    var locationHint = document.getElementById('gps-location-hint');
    var locationSubmit = document.getElementById('gps_location_enabled_submit');
    if (!container) return;

    function escapeHtml(s) {
      var d = document.createElement('div');
      d.textContent = s;
      return d.innerHTML;
    }

    function renderStatus(data) {
      var gpsConnected = data.gpsd_connected || (data.serial_ports_with_gps && data.serial_ports_with_gps.length > 0);
      var hasFix = data.gpsd_has_fix || (data.serial_ports_with_gps && data.serial_ports_with_gps.length > 0);

      if (gpsSection) gpsSection.style.display = 'block';  // Always show config
      if (gpsNoConnect) gpsNoConnect.style.display = gpsConnected ? 'none' : 'block';

      if (locationToggle && locationHint) {
        if (hasFix) {
          locationToggle.disabled = false;
          locationHint.textContent = 'GPS has fix. You can use GPS for default location.';
          locationHint.style.color = '#0f0';
        } else {
          locationToggle.disabled = true;
          locationToggle.value = '0';
          if (locationSubmit) locationSubmit.value = '0';
          locationHint.textContent = 'No GPS fix. Enter manual location above.';
          locationHint.style.color = '#888';
        }
      }
      if (locationToggle && locationSubmit && !locationToggle.disabled) {
        locationSubmit.value = locationToggle.value;
      }

      if (!gpsConnected) {
        container.innerHTML = '<div class="gps-status-box gps-status-warning"><div class="gps-status-title">No GPS detected</div><p>Configure connection method below. Connect a USB GPS receiver and click Refresh.</p></div>';
      } else {
      var statusText = hasFix ? 'Active – fix acquired' : 'Waiting for fix';
      var boxClass = hasFix ? 'ok' : 'warning';
      var html = '<div class="gps-status-box gps-status-' + boxClass + '"><div class="gps-status-title">Status: ' + escapeHtml(statusText) + '</div>';
      if (data.methods && data.methods.length > 0) {
        html += '<ul class="gps-devices-list">';
        data.methods.forEach(function(m) {
          var badge = m.working ? (m.has_fix ? 'Active' : 'Waiting') : (m.available ? 'Not running' : 'Unavailable');
          html += '<li><strong>' + escapeHtml(m.name) + '</strong>: ' + escapeHtml(m.detail) + ' <span style="color:#888;">(' + badge + ')</span></li>';
        });
        html += '</ul>';
      }
      html += '</div>';
      container.innerHTML = html;
      }

      if (sourceSelect && portRow && portSelect) {
        sourceSelect.value = data.gps_source || 'auto';
        portRow.style.display = sourceSelect.value === 'serial' ? 'block' : 'none';
        portSelect.innerHTML = '<option value="">-- Select port --</option>';
        var ports = data.serial_ports_with_gps || data.devices || [];
        if (ports.length === 0) ports = data.devices || [];
        ports.forEach(function(p) {
          var path = typeof p === 'string' ? p : (p.path || p.device);
          if (path) {
            var opt = document.createElement('option');
            opt.value = path;
            opt.textContent = path;
            if (path === (data.gps_serial_port || '')) opt.selected = true;
            portSelect.appendChild(opt);
          }
        });
      }
    }

    function loadStatus() {
      if (gpsSection) gpsSection.style.display = 'block';
      if (gpsNoConnect) gpsNoConnect.style.display = 'none';
      if (container) container.innerHTML = '<p class="gps-loading">Checking GPS status...</p>';
      if (refreshBtn) refreshBtn.disabled = true;
      fetch('/api/gps/status')
        .then(function(r) { return r.json(); })
        .then(function(data) {
          renderStatus(data);
          if (refreshBtn) refreshBtn.disabled = false;
        })
        .catch(function() {
          if (container) container.innerHTML = '<div class="gps-status-box gps-status-error"><div class="gps-status-title">Error</div><p>Failed to check GPS status.</p></div>';
          if (gpsSection) gpsSection.style.display = 'block';
          if (gpsNoConnect) gpsNoConnect.style.display = 'none';
          if (refreshBtn) refreshBtn.disabled = false;
        });
    }

    window._gpsLoadOnShow = loadStatus;
    if (refreshBtn) refreshBtn.addEventListener('click', loadStatus);
    if (refreshNoConnectBtn) refreshNoConnectBtn.addEventListener('click', loadStatus);
    if (sourceSelect) sourceSelect.addEventListener('change', function() {
      if (portRow) portRow.style.display = sourceSelect.value === 'serial' ? 'block' : 'none';
    });
    if (locationToggle && locationSubmit) {
      locationToggle.addEventListener('change', function() {
        if (!locationToggle.disabled) locationSubmit.value = locationToggle.value;
      });
    }
    var setupForm = document.getElementById('setup-form');
    if (setupForm && locationToggle && locationSubmit) {
      setupForm.addEventListener('submit', function() {
        locationSubmit.value = locationToggle.disabled ? '0' : locationToggle.value;
      });
    }
    loadStatus();
  }

  function initializeSetup() {
    initializeEventListeners();
    updatePreview();
    initGpsTab();
    var match = /[?&]tab=([^&]+)/.exec(window.location.search || '');
    if (match && (match[1] === 'gps' || match[1] === 'hardware')) showSetupPage(1);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeSetup);
  } else {
    initializeSetup();
  }
})();
