/*
  Module JS. Loaded once per page; runs in the main document.

  FINDING CELLS:
  - The core gives each cell the class .grid-cell-{id} (e.g. .grid-cell-example).
  - Use document.querySelectorAll('.grid-cell-{id}') to get every cell
    that has this module, then update each one.

  NAMING:
  - Use the same ModuleName_ classes you used in index.html (e.g. .example_label)
    when querying inside a cell with cell.querySelector('.example_label').

  SETTINGS (if your module has settings):
  - Per-cell settings are in window.GLANCERF_MODULE_SETTINGS.
  - Key is "row_col" (e.g. "0_1"). Value is an object of setting id -> value.
*/
(function() {
    document.querySelectorAll('.grid-cell-example').forEach(function(el) {
        var label = el.querySelector('.example_label');
        if (label) console.log('Example module mounted', label);
    });
})();
