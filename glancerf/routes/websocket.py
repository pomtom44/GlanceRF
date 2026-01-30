"""
WebSocket routes for GlanceRF
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from glancerf.websocket_manager import ConnectionManager


def register_websocket_routes(app: FastAPI, connection_manager: ConnectionManager):
    """Register WebSocket routes"""
    
    @app.websocket("/ws/desktop")
    async def websocket_desktop(websocket: WebSocket):
        """WebSocket endpoint for desktop app (source of truth)"""
        await connection_manager.connect_desktop(websocket)

        try:
            while True:
                data = await websocket.receive_json()
                msg_type = data.get("type")
                if msg_type in ["state", "update", "dom"]:
                    await connection_manager.broadcast_from_desktop(data)
                    connection_manager.desktop_state = data.get("data", {})
                elif msg_type == "desktop_size":
                    # Desktop window size: store and broadcast so browsers match this aspect ratio
                    w = data.get("width")
                    h = data.get("height")
                    if w is not None and h is not None and w > 0 and h > 0:
                        connection_manager.desktop_state["desktop_width"] = int(w)
                        connection_manager.desktop_state["desktop_height"] = int(h)
                    else:
                        connection_manager.desktop_state.pop("desktop_width", None)
                        connection_manager.desktop_state.pop("desktop_height", None)
                    await connection_manager.broadcast_from_desktop({
                        "type": "state",
                        "data": dict(connection_manager.desktop_state)
                    })
        except WebSocketDisconnect:
            await connection_manager.disconnect(websocket)
        except Exception:
            await connection_manager.disconnect(websocket)
    
    
    @app.websocket("/ws/browser")
    async def websocket_browser(websocket: WebSocket):
        """WebSocket endpoint for web browsers (two-way mirroring)"""
        await connection_manager.connect_browser(websocket)

        try:
            while True:
                try:
                    data = await websocket.receive_json()
                    if data.get("type") in ["state", "update", "dom"]:
                        await connection_manager.broadcast_from_browser(data, websocket)
                except ValueError:
                    await websocket.receive_text()
        except WebSocketDisconnect:
            await connection_manager.disconnect(websocket)
        except Exception:
            await connection_manager.disconnect(websocket)
