/* GlanceRF menu - open via right-click, M key, or hamburger button */

(function () {
  'use strict';

  var menu = document.getElementById('glancerf-menu');
  var overlay = document.getElementById('glancerf-menu-overlay');

  function openMenu() {
    if (menu) menu.classList.add('open');
  }

  function closeMenu() {
    if (menu) menu.classList.remove('open');
  }

  function toggleMenu() {
    if (menu) menu.classList.toggle('open');
  }

  document.addEventListener('DOMContentLoaded', function () {
    if (overlay) overlay.addEventListener('click', closeMenu);

    /* Right-click opens menu */
    document.addEventListener('contextmenu', function (e) {
      e.preventDefault();
      openMenu();
    });

    /* M key toggles menu, Escape closes; On The Air shortcut (skip when typing in inputs) */
    document.addEventListener('keydown', function (e) {
      var active = document.activeElement;
      var isInput = active && (active.tagName === 'INPUT' || active.tagName === 'TEXTAREA' || active.tagName === 'SELECT' || active.isContentEditable);
      if (isInput) return;
      var otaShortcut = (typeof window.GLANCERF_ON_THE_AIR_SHORTCUT === 'string' ? window.GLANCERF_ON_THE_AIR_SHORTCUT : '').trim();
      if (otaShortcut && e.key === otaShortcut) {
        e.preventDefault();
        window.GLANCERF_ON_THE_AIR = !window.GLANCERF_ON_THE_AIR;
        window.dispatchEvent(new CustomEvent('glancerf_on_the_air', { detail: { value: window.GLANCERF_ON_THE_AIR } }));
        return;
      }
      if (e.key === 'm' || e.key === 'M') {
        e.preventDefault();
        toggleMenu();
      } else if (e.key === 'Escape') {
        if (menu && menu.classList.contains('open')) {
          e.preventDefault();
          closeMenu();
        }
      }
    });

    var restartBtn = document.getElementById('menu-restart-services');
    if (restartBtn) {
      restartBtn.addEventListener('click', function () {
        fetch('/api/restart', { method: 'POST' })
          .then(function (r) { return r.json(); })
          .then(function (data) {
            if (data.success) {
              restartBtn.disabled = true;
              restartBtn.textContent = 'Restarting...';
            } else if (data.message) {
              alert(data.message);
            }
          })
          .catch(function () { alert('Restart request failed'); });
      });
    }

  });
})();
