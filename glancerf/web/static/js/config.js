(function() {
    document.addEventListener('keydown', function(event) {
        var isInputFocused = document.activeElement && (
            document.activeElement.tagName === 'INPUT' ||
            document.activeElement.tagName === 'SELECT' ||
            document.activeElement.tagName === 'TEXTAREA' ||
            document.activeElement.isContentEditable
        );
        if (isInputFocused) return;
        if (event.key === 's' || event.key === 'S') {
            window.location.href = '/setup';
            return;
        }
        if (event.key === 'l' || event.key === 'L') {
            window.location.href = '/layout';
            return;
        }
        if (event.key === 'm' || event.key === 'M') {
            window.location.href = '/modules';
            return;
        }
        if (event.key === 'c' || event.key === 'C') {
            window.location.href = '/config';
            return;
        }
    });
})();
