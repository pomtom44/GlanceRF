/*
  Module JS. Loaded once per page.
  Find cells via .grid-cell-{id}, update content, handle settings.
*/
(function () {
  'use strict';
  document.querySelectorAll('.grid-cell-example').forEach(function (el) {
    var label = el.querySelector('.example_label');
    if (label) {
      // Example: could update from GLANCERF_MODULE_SETTINGS or API
      label.textContent = 'Example';
    }
  });
})();
