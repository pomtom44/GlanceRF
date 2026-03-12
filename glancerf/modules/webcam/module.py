"""Video feed from local webcam (this device or server) or a remote URL. Local (this device) is only visible on the browser where the camera is connected. Local (server) requires ffmpeg installed on the server."""

from glancerf.modules.loader import load_assets

inner_html, css, js = load_assets(__file__)

MODULE = {
    "id": "webcam",
    "name": "Webcam",
    "color": "#0d1117",
    "inner_html": inner_html,
    "css": css,
    "js": js,
    "settings": [
        {"id": "source_type", "label": "Source", "type": "select", "options": [
            {"value": "local_user", "label": "Local (this device)"},
            {"value": "local_server", "label": "Local (server)"},
            {"value": "remote", "label": "Remote (URL / IP)"},
        ], "default": "local_user"},
        {"id": "device_id", "label": "Camera", "type": "webcam_local_devices", "default": "", "show_when_source": "local_user"},
        {"id": "device_index", "label": "Camera", "type": "webcam_server_devices", "default": "0", "show_when_source": "local_server"},
        {"id": "remote_url", "label": "URL or IP", "type": "text", "default": "", "placeholder": "https://... or http://...", "show_when_source": "remote"},
        {"id": "remote_type", "label": "Stream type", "type": "select", "options": [
            {"value": "mjpeg", "label": "MJPEG"},
            {"value": "video", "label": "Video URL"},
        ], "default": "mjpeg", "show_when_source": "remote"},
    ],
    "gpio": {
        "inputs": [{"id": "start_stop", "name": "Start/Stop stream"}],
        "outputs": [{"id": "led", "name": "Stream active LED"}],
    },
}


def _on_gpio_start_stop(value: bool) -> None:
    """GPIO input: Start/Stop stream. UI receives gpio_input WebSocket and can toggle stream (e.g. show/hide video)."""
    pass


GPIO_INPUT_HANDLERS = {"start_stop": _on_gpio_start_stop}
