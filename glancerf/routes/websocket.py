"""
WebSocket routes for GlanceRF
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from glancerf.websocket_manager import ConnectionManager
from glancerf.logging_config import DETAILED_LEVEL, get_logger

_log = get_logger("websocket")


def register_websocket_routes(app: FastAPI, connection_manager: ConnectionManager):
    """Register WebSocket routes"""

    @app.websocket("/ws/desktop")
    async def websocket_desktop(websocket: WebSocket):
        """WebSocket endpoint for desktop app (source of truth)"""
        _log.log(DETAILED_LEVEL, "WebSocket: desktop connected")
        await connection_manager.connect_desktop(websocket)
        try:
            while True:
                data = await websocket.receive_json()
                msg_type = data.get("type")
                _log.debug("WebSocket desktop received type=%s", msg_type)
                if msg_type in ["state", "update"]:
                    await connection_manager.broadcast_from_desktop(data)
                    connection_manager.desktop_state = data.get("data", {})
                elif msg_type == "dom":
                    pass
        except WebSocketDisconnect:
            _log.log(DETAILED_LEVEL, "WebSocket: desktop disconnected")
            await connection_manager.disconnect(websocket)
        except Exception as e:
            _log.debug("WebSocket desktop error: %s", e)
            await connection_manager.disconnect(websocket)

    @app.websocket("/ws/browser")
    async def websocket_browser(websocket: WebSocket):
        """WebSocket endpoint for web browsers (two-way mirroring)"""
        _log.log(DETAILED_LEVEL, "WebSocket: browser connected")
        await connection_manager.connect_browser(websocket)
        try:
            while True:
                try:
                    data = await websocket.receive_json()
                    msg_type = data.get("type")
                    _log.debug("WebSocket browser received type=%s", msg_type)
                    if data.get("type") in ["state", "update"]:
                        await connection_manager.broadcast_from_browser(data, websocket)
                except ValueError:
                    await websocket.receive_text()
        except WebSocketDisconnect:
            _log.log(DETAILED_LEVEL, "WebSocket: browser disconnected")
            await connection_manager.disconnect(websocket)
        except Exception as e:
            _log.debug("WebSocket browser error: %s", e)
            await connection_manager.disconnect(websocket)

    @app.websocket("/ws/readonly")
    async def websocket_readonly(websocket: WebSocket):
        """WebSocket endpoint for read-only portal (receives config_update only)."""
        _log.log(DETAILED_LEVEL, "WebSocket: readonly connected")
        await connection_manager.connect_readonly(websocket)
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            _log.log(DETAILED_LEVEL, "WebSocket: readonly disconnected")
            await connection_manager.disconnect(websocket)
        except Exception as e:
            _log.debug("WebSocket readonly error: %s", e)
            await connection_manager.disconnect(websocket)
