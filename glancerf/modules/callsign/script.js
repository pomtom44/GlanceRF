(function() {
    function updateCallsigns() {
        var allSettings = window.GLANCERF_MODULE_SETTINGS || {};
        document.querySelectorAll('.grid-cell-callsign').forEach(function(cell) {
            var r = cell.getAttribute('data-row');
            var c = cell.getAttribute('data-col');
            var cellKey = (r != null && c != null) ? r + '_' + c : '';
            var ms = (cellKey && allSettings[cellKey]) ? allSettings[cellKey] : {};
            var call = (ms.callsign || window.GLANCERF_SETUP_CALLSIGN || '').toString().trim();
            var grid = (ms.grid || window.GLANCERF_SETUP_LOCATION || '').toString().trim();
            var comment = (ms.comment || '').toString().trim();
            var callEl = cell.querySelector('.callsign_line');
            var gridEl = cell.querySelector('.callsign_grid');
            var commentEl = cell.querySelector('.callsign_comment');
            if (callEl) {
                callEl.textContent = call || 'Callsign';
                callEl.style.display = call ? '' : 'none';
            }
            if (gridEl) {
                gridEl.textContent = grid ? (grid.length <= 6 ? 'Grid: ' + grid.toUpperCase() : grid) : '';
                gridEl.style.display = grid ? '' : 'none';
            }
            if (commentEl) {
                commentEl.textContent = comment;
                commentEl.style.display = comment ? '' : 'none';
            }
        });
    }
    updateCallsigns();
})();
