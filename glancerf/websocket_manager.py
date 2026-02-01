"""
WebSocket connection manager for real-time mirroring
"""

from typing import List

from fastapi import WebSocket


class ConnectionManager:
    """Manages WebSocket connections for desktop mirroring"""
    def __init__(self):
        self.desktop_connection: WebSocket = None
        self.browser_connections: List[WebSocket] = []
        self.desktop_state = {}
    
    async def connect_desktop(self, websocket: WebSocket):
        """Register desktop app connection"""
        await websocket.accept()
        self.desktop_connection = websocket
    
    async def connect_browser(self, websocket: WebSocket):
        """Register web browser connection"""
        await websocket.accept()
        self.browser_connections.append(websocket)
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
            for conn in list(self.browser_connections):
                try:
                    await conn.send_json({"type": "state", "data": dict(self.desktop_state)})
                except Exception:
                    pass
        elif websocket in self.browser_connections:
            self.browser_connections.remove(websocket)
    
    async def broadcast_from_desktop(self, message: dict):
        """Broadcast message from desktop to all browsers"""
        self.desktop_state = message.get("data", {})
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
        # Update desktop state
        self.desktop_state = message.get("data", {})
        
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
