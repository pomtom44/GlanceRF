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

  var nextBtn = document.getElementById('setup-next-btn');
  var nextBtn2 = document.getElementById('setup-next-btn-2');
  var backBtn = document.getElementById('setup-back-btn');
  var backBtn3 = document.getElementById('setup-back-btn-3');
  var tab1 = document.getElementById('tab-page-1');
  var tab2 = document.getElementById('tab-page-2');
  var tab3 = document.getElementById('tab-page-3');
  if (nextBtn) nextBtn.addEventListener('click', function () { showSetupPage(2); });
  if (nextBtn2) nextBtn2.addEventListener('click', function () { showSetupPage(3); });
  if (backBtn) backBtn.addEventListener('click', function () { showSetupPage(1); });
  if (backBtn3) backBtn3.addEventListener('click', function () { showSetupPage(2); });
  if (tab1) tab1.addEventListener('click', function () { showSetupPage(1); });
  if (tab2) tab2.addEventListener('click', function () { showSetupPage(2); });
  if (tab3) tab3.addEventListener('click', function () { showSetupPage(3); });

  function initializeSetup() {
    initializeEventListeners();
    updatePreview();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeSetup);
  } else {
    initializeSetup();
  }
})();
