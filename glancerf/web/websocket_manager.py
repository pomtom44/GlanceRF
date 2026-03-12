"""
WebSocket connection manager for real-time desktop/browser mirroring.
"""

from typing import List

from fastapi import WebSocket

from glancerf.config import get_logger

_log = get_logger("websocket_manager")


class ConnectionManager:
    """Manages WebSocket connections for desktop mirroring."""

    def __init__(self):
        self.desktop_connection: WebSocket = None
        self.browser_connections: List[WebSocket] = []
        self.readonly_connections: List[WebSocket] = []
        self.desktop_state = {}

    async def _send_to_connections(self, connections: list, message: dict) -> None:
        """Send message to connections, removing any that fail."""
        disconnected = []
        for conn in list(connections):
            try:
                await conn.send_json(message)
            except Exception:
                disconnected.append(conn)
        for conn in disconnected:
            if conn in connections:
                connections.remove(conn)

    async def _broadcast_to_all(self, message: dict) -> None:
        """Send message to desktop, browsers, and readonly."""
        if self.desktop_connection:
            try:
                await self.desktop_connection.send_json(message)
            except Exception:
                self.desktop_connection = None
        await self._send_to_connections(self.browser_connections, message)
        await self._send_to_connections(self.readonly_connections, message)

    async def connect_readonly(self, websocket: WebSocket):
        await websocket.accept()
        self.readonly_connections.append(websocket)
        _log.debug("readonly_connections count=%s", len(self.readonly_connections))

    async def connect_desktop(self, websocket: WebSocket):
        await websocket.accept()
        self.desktop_connection = websocket
        _log.debug("desktop connected")

    async def connect_browser(self, websocket: WebSocket):
        await websocket.accept()
        self.browser_connections.append(websocket)
        _log.debug("browser connected, total browsers=%s", len(self.browser_connections))
        if self.desktop_state:
            try:
                await websocket.send_json({"type": "state", "data": self.desktop_state})
            except Exception:
                pass

    async def disconnect(self, websocket: WebSocket):
        if websocket == self.desktop_connection:
            self.desktop_connection = None
            _log.debug("desktop disconnected")
            for conn in list(self.browser_connections):
                try:
                    await conn.send_json({"type": "state", "data": dict(self.desktop_state)})
                except Exception:
                    pass
        elif websocket in self.browser_connections:
            self.browser_connections.remove(websocket)
            _log.debug("browser disconnected, remaining=%s", len(self.browser_connections))
        elif websocket in self.readonly_connections:
            self.readonly_connections.remove(websocket)
            _log.debug("readonly disconnected, remaining=%s", len(self.readonly_connections))

    async def broadcast_from_desktop(self, message: dict):
        self.desktop_state = message.get("data", {})
        _log.debug("broadcast_from_desktop to %s browsers", len(self.browser_connections))
        await self._send_to_connections(self.browser_connections, message)

    async def broadcast_from_browser(self, message: dict, sender_websocket: WebSocket):
        self.desktop_state = message.get("data", {})
        _log.debug("broadcast_from_browser to desktop + other browsers")
        if self.desktop_connection:
            try:
                await self.desktop_connection.send_json(message)
            except Exception:
                self.desktop_connection = None
        disconnected = []
        for connection in self.browser_connections:
            if sender_websocket is None or connection != sender_websocket:
                try:
                    await connection.send_json(message)
                except Exception:
                    disconnected.append(connection)
        for conn in disconnected:
            if conn in self.browser_connections:
                self.browser_connections.remove(conn)

    async def broadcast_config_update(self, data: dict = None):
        """Broadcast config_update to desktop, browsers, and readonly so they reload."""
        msg = {"type": "config_update", "data": data or {"reload": True}}
        _log.debug("broadcast_config_update")
        await self._broadcast_to_all(msg)

    async def broadcast_update_notification(self, message: dict):
        """Broadcast update_available to desktop, browsers, and readonly."""
        _log.debug("broadcast_update_notification")
        await self._broadcast_to_all(message)

    async def broadcast_gpio_input(self, module_id: str, function_id: str, value: bool):
        """Broadcast GPIO input event to browsers (and desktop if connected)."""
        msg = {
            "type": "gpio_input",
            "data": {"module_id": module_id, "function_id": function_id, "value": value},
        }
        await self._broadcast_to_all(msg)

    async def broadcast_aprs_update(self):
        """Broadcast aprs_update so clients refetch APRS data (real-time trigger)."""
        await self._broadcast_to_all({"type": "aprs_update"})
