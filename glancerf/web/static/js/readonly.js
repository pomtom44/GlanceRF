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
