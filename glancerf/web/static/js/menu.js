(function() {
    function initRestartButton() {
        var btn = document.getElementById('menu-restart-services');
        if (!btn) return;
        btn.addEventListener('click', function() {
            var menu = document.getElementById('glancerf-menu');
            if (menu) menu.classList.remove('open');
            btn.disabled = true;
            var originalText = btn.textContent;
            btn.textContent = 'Restarting...';
            fetch('/api/restart', { method: 'POST', headers: { 'Content-Type': 'application/json' } })
                .then(function(r) { return r.json(); })
                .then(function(data) {
                    if (data.success) {
                        btn.textContent = 'Restarting...';
                    } else {
                        btn.disabled = false;
                        btn.textContent = originalText;
                        alert(data.message || 'Restart failed.');
                    }
                })
                .catch(function() {
                    btn.disabled = false;
                    btn.textContent = originalText;
                    alert('Restart request failed.');
                });
        });
    }
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initRestartButton);
    } else {
        initRestartButton();
    }
})();
