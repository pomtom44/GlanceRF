(function() {
    var TYPE_LOCAL = 'webcam_local_devices';
    var TYPE_SERVER = 'webcam_server_devices';

    function fillLocalDevices(container) {
        var ui = container.querySelector('.cell-setting-custom-ui');
        var hidden = container.querySelector('.cell-setting-custom-value');
        if (!ui || !hidden || ui.getAttribute('data-filled') === '1') return;
        ui.setAttribute('data-filled', '1');
        var currentValue = (container.getAttribute('data-current-value') || '').trim();
        ui.style.fontSize = '12px';

        var sel = document.createElement('select');
        sel.className = 'cell-setting-select';
        sel.style.width = '100%';
        sel.style.fontSize = '12px';
        sel.style.padding = '4px';

        function addOption(value, label) {
            var opt = document.createElement('option');
            opt.value = value;
            opt.textContent = label;
            if (value === currentValue) opt.selected = true;
            sel.appendChild(opt);
        }
        addOption('', 'Default camera');
        ui.appendChild(sel);

        function syncHidden() {
            hidden.value = sel.value;
        }

        if (!navigator.mediaDevices || !navigator.mediaDevices.enumerateDevices) {
            ui.insertBefore(document.createTextNode('Camera list not available in this browser.'), sel);
            return;
        }
        navigator.mediaDevices.enumerateDevices().then(function(devices) {
            var videoInputs = devices.filter(function(d) { return d.kind === 'videoinput'; });
            videoInputs.forEach(function(d) {
                var opt = document.createElement('option');
                opt.value = d.deviceId;
                opt.textContent = d.label || ('Camera ' + (sel.options.length));
                if (d.deviceId === currentValue) opt.selected = true;
                sel.appendChild(opt);
            });
            syncHidden();
            sel.addEventListener('change', syncHidden);
        }).catch(function() {
            ui.insertBefore(document.createTextNode('Could not list cameras.'), sel);
        });
    }

    function fillServerDevices(container) {
        var ui = container.querySelector('.cell-setting-custom-ui');
        var hidden = container.querySelector('.cell-setting-custom-value');
        if (!ui || !hidden || ui.getAttribute('data-filled') === '1') return;
        ui.setAttribute('data-filled', '1');
        var currentValue = (container.getAttribute('data-current-value') || '0').trim();
        ui.style.fontSize = '12px';
        ui.textContent = 'Loading...';

        fetch('/api/webcam/devices').then(function(r) { return r.json(); }).then(function(data) {
            ui.innerHTML = '';
            var list = (data && data.devices) ? data.devices : [];
            var sel = document.createElement('select');
            sel.className = 'cell-setting-select';
            sel.style.width = '100%';
            sel.style.fontSize = '12px';
            sel.style.padding = '4px';
            if (list.length === 0) {
                sel.appendChild(new Option('No cameras found', '0'));
            } else {
                list.forEach(function(d) {
                    var opt = document.createElement('option');
                    opt.value = String(d.index);
                    opt.textContent = d.name || ('Device ' + d.index);
                    if (String(d.index) === currentValue) opt.selected = true;
                    sel.appendChild(opt);
                });
            }
            hidden.value = sel.value;
            sel.addEventListener('change', function() {
                hidden.value = sel.value;
            });
            ui.appendChild(sel);
        }).catch(function() {
            ui.innerHTML = '';
            ui.appendChild(document.createTextNode('Could not load server cameras.'));
        });
    }

    function run() {
        document.querySelectorAll('.cell-setting-custom[data-setting-type="' + TYPE_LOCAL + '"]').forEach(fillLocalDevices);
        document.querySelectorAll('.cell-setting-custom[data-setting-type="' + TYPE_SERVER + '"]').forEach(fillServerDevices);
    }

    run();
    document.addEventListener('glancerf-cell-settings-updated', function() { run(); });
})();
