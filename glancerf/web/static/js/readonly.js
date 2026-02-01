// Read-only view: no WebSocket, no desktop/browser sync. Sizing is viewport-only (no shared state with main).
document.addEventListener('keydown', function(e) {
    e.preventDefault();
    e.stopPropagation();
    return false;
}, true);

document.addEventListener('keyup', function(e) {
    e.preventDefault();
    e.stopPropagation();
    return false;
}, true);

document.addEventListener('click', function(e) {
    e.preventDefault();
    e.stopPropagation();
    return false;
}, true);

document.addEventListener('contextmenu', function(e) {
    e.preventDefault();
    return false;
}, true);

document.onselectstart = function() {
    return false;
};

document.onmousedown = function() {
    return false;
};
