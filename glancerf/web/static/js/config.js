(function() {
    document.addEventListener('keydown', function(event) {
        var isInputFocused = document.activeElement && (
            document.activeElement.tagName === 'INPUT' ||
            document.activeElement.tagName === 'SELECT' ||
            document.activeElement.tagName === 'TEXTAREA' ||
            document.activeElement.isContentEditable
        );
        if (isInputFocused) return;
        if (event.key === 'm' || event.key === 'M') {
            event.preventDefault();
            var menu = document.getElementById('glancerf-menu');
            if (menu) menu.classList.toggle('open');
            return;
        }
        if (event.key === 'Escape') {
            var menu = document.getElementById('glancerf-menu');
            if (menu && menu.classList.contains('open')) {
                menu.classList.remove('open');
                event.preventDefault();
            }
        }
    });

    var overlay = document.getElementById('glancerf-menu-overlay');
    if (overlay) overlay.addEventListener('click', function() {
        var menu = document.getElementById('glancerf-menu');
        if (menu) menu.classList.remove('open');
    });
})();
