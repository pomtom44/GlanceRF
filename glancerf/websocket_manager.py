"""
WebSocket connection manager for real-time mirroring
"""

from typing import List

from fastapi import WebSocket

from glancerf.logging_config import get_logger

_log = get_logger("websocket_manager")


class ConnectionManager:
    """Manages WebSocket connections for desktop mirroring"""
    def __init__(self):
        self.desktop_connection: WebSocket = None
        self.browser_connections: List[WebSocket] = []
        self.readonly_connections: List[WebSocket] = []
        self.desktop_state = {}

    async def connect_readonly(self, websocket: WebSocket):
        """Register read-only portal connection (receives config_update only)."""
        await websocket.accept()
        self.readonly_connections.append(websocket)
        _log.debug("readonly_connections count=%s", len(self.readonly_connections))

    async def connect_desktop(self, websocket: WebSocket):
        """Register desktop app connection"""
        await websocket.accept()
        self.desktop_connection = websocket
        _log.debug("desktop connected")

    async def connect_browser(self, websocket: WebSocket):
        """Register web browser connection"""
        await websocket.accept()
        self.browser_connections.append(websocket)
        _log.debug("browser connected, total browsers=%s", len(self.browser_connections))
        # Send current desktop state if available
        if self.desktop_state:
            try:
                await websocket.send_json({
                    "type": "state",
                    "data": self.desktop_state
                })
            except Exception:
                pass
    
    async def disconnect(self, websocket: WebSocket):
        """Remove connection"""
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
        """Broadcast message from desktop to all browsers"""
        self.desktop_state = message.get("data", {})
        _log.debug("broadcast_from_desktop to %s browsers", len(self.browser_connections))
        # Send to all browser connections
        disconnected = []
        for connection in self.browser_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        
        # Remove disconnected connections
        for conn in disconnected:
            if conn in self.browser_connections:
                self.browser_connections.remove(conn)
    
    async def broadcast_from_browser(self, message: dict, sender_websocket: WebSocket):
        """Broadcast message from a browser to desktop and all other browsers"""
        self.desktop_state = message.get("data", {})
        _log.debug("broadcast_from_browser to desktop + %s other browsers", len(self.browser_connections) - (1 if sender_websocket and sender_websocket in self.browser_connections else 0))
        
        # Send to desktop app if connected
        if self.desktop_connection:
            try:
                await self.desktop_connection.send_json(message)
            except Exception:
                self.desktop_connection = None
        
        # Send to all browser connections (excluding sender if specified)
        disconnected = []
        for connection in self.browser_connections:
            if sender_websocket is None or connection != sender_websocket:
                try:
                    await connection.send_json(message)
                except Exception:
                    disconnected.append(connection)
        
        # Remove disconnected connections
        for conn in disconnected:
            if conn in self.browser_connections:
                self.browser_connections.remove(conn)
    
    async def broadcast_update_notification(self, message: dict):
        """Broadcast update notification to all connected clients."""
        _log.debug("broadcast_update_notification to desktop + %s browsers", len(self.browser_connections))
        # Send to desktop
        if self.desktop_connection:
            try:
                await self.desktop_connection.send_json(message)
            except Exception:
                self.desktop_connection = None
        
        # Send to all browsers
        disconnected = []
        for connection in self.browser_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        
        # Remove disconnected connections
        for conn in disconnected:
            if conn in self.browser_connections:
                self.browser_connections.remove(conn)
