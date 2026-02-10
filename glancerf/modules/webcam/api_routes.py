"""
Webcam module API: MJPEG stream from a camera attached to the server.
Uses ffmpeg (subprocess, no Python deps). Requires ffmpeg on PATH.
Cross-OS: Linux (v4l2), Windows (dshow), macOS (avfoundation).
"""

import asyncio
import platform
import re

from fastapi import FastAPI, Query
from fastapi.responses import Response, StreamingResponse

from glancerf.config import get_logger

_log = get_logger("webcam.api_routes")

_BOUNDARY = "glancerf-webcam"
_MJPEG_CONTENT_TYPE = "multipart/x-mixed-replace; boundary=" + _BOUNDARY
_JPEG_SOI = bytes((0xFF, 0xD8))
_JPEG_EOI = bytes((0xFF, 0xD9))


async def _check_ffmpeg() -> str | None:
    """Return None if ffmpeg is available, else error message."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "ffmpeg", "-version",
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await proc.wait()
        if proc.returncode != 0:
            return "ffmpeg is not available."
        return None
    except FileNotFoundError:
        return "ffmpeg needs to be installed on the server."


async def _list_windows_dshow_devices() -> list[dict]:
    """Run ffmpeg -list_devices dshow, return [{"index": 0, "name": "..."}, ...]."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "ffmpeg", "-list_devices", "true", "-f", "dshow", "-i", "dummy",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        text = (stderr or b"").decode("utf-8", errors="replace")
    except Exception:
        return []
    devices = []
    in_video = False
    for line in text.splitlines():
        if "DirectShow video devices" in line:
            in_video = True
            continue
        if in_video and "DirectShow audio" in line:
            break
        if in_video:
            m = re.search(r'^\s*"([^"]+)"\s*$', line)
            if m and not line.strip().startswith("Alternative"):
                devices.append({"index": len(devices), "name": m.group(1)})
    return devices


async def _get_windows_dshow_device_name(device_index: int) -> str | None:
    """Return name at index from dshow list, or None."""
    devices = await _list_windows_dshow_devices()
    for d in devices:
        if d["index"] == device_index:
            return d["name"]
    return None


def _build_ffmpeg_cmd(device_index: int, windows_device_name: str | None = None):
    idx = max(0, min(device_index, 4))
    system = platform.system()
    if system == "Linux":
        return [
            "ffmpeg", "-f", "v4l2", "-i", f"/dev/video{idx}",
            "-vf", "scale=640:-1", "-r", "10",
            "-f", "image2pipe", "-vcodec", "mjpeg", "-q:v", "5", "-",
        ]
    if system == "Darwin":
        return [
            "ffmpeg", "-f", "avfoundation", "-framerate", "10", "-i", f"{idx}:none",
            "-vf", "scale=640:-1",
            "-f", "image2pipe", "-vcodec", "mjpeg", "-q:v", "5", "-",
        ]
    if system == "Windows" and windows_device_name:
        return [
            "ffmpeg", "-f", "dshow", "-i", f"video={windows_device_name}",
            "-vf", "scale=640:-1", "-r", "10",
            "-f", "image2pipe", "-vcodec", "mjpeg", "-q:v", "5", "-",
        ]
    return None


async def _stream_mjpeg(device_index: int):
    cmd = None
    if platform.system() == "Windows":
        name = await _get_windows_dshow_device_name(device_index)
        cmd = _build_ffmpeg_cmd(device_index, name)
    else:
        cmd = _build_ffmpeg_cmd(device_index)
    if not cmd:
        return
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
    except FileNotFoundError:
        _log.warning("webcam stream: ffmpeg not found")
        return
    except Exception as e:
        _log.debug("webcam stream subprocess error: %s", e)
        return
    try:
        try:
            from glancerf.gpio import set_output
            set_output("webcam", "led", True)
        except Exception:
            pass
        buf = b""
        while True:
            chunk = await proc.stdout.read(4096)
            if not chunk:
                break
            buf += chunk
            while True:
                start = buf.find(_JPEG_SOI)
                end = buf.find(_JPEG_EOI)
                if start == -1:
                    buf = buf[-1:] if len(buf) > 1 else b""
                    break
                if end == -1 or end < start:
                    break
                end += len(_JPEG_EOI)
                frame = buf[start:end]
                buf = buf[end:]
                part = (
                    b"--" + _BOUNDARY.encode() + b"\r\n"
                    b"Content-Type: image/jpeg\r\nContent-Length: " + str(len(frame)).encode() + b"\r\n\r\n"
                    + frame + b"\r\n"
                )
                yield part
    finally:
        try:
            from glancerf.gpio import set_output
            set_output("webcam", "led", False)
        except Exception:
            pass
        try:
            proc.kill()
            await proc.wait()
        except Exception:
            pass


async def _check_device(device_index: int) -> str | None:
    """Return None if device is usable, else error message."""
    system = platform.system()
    idx = max(0, min(device_index, 4))
    if system == "Linux":
        dev = f"/dev/video{idx}"
        try:
            with open(dev, "rb") as f:
                pass
        except OSError:
            return f"Device {dev} not found or not readable."
        return None
    if system == "Windows":
        name = await _get_windows_dshow_device_name(device_index)
        if not name:
            return f"No DirectShow video device at index {device_index}. Install ffmpeg and ensure a camera is connected."
        return None
    if system == "Darwin":
        return None
    return "Unsupported platform."


async def _list_server_devices() -> list[dict]:
    """Return list of server cameras for dropdown: [{"index": 0, "name": "..."}, ...]."""
    system = platform.system()
    if system == "Windows":
        return await _list_windows_dshow_devices()
    if system == "Linux":
        out = []
        for i in range(5):
            out.append({"index": i, "name": "Video " + str(i)})
        return out
    if system == "Darwin":
        out = []
        for i in range(5):
            out.append({"index": i, "name": "Camera " + str(i)})
        return out
    return []


def register_routes(app: FastAPI) -> None:
    """Register GET /api/webcam/stream and GET /api/webcam/devices."""

    @app.get("/api/webcam/devices")
    async def webcam_devices():
        """Return list of server cameras for layout dropdown: [{"index": 0, "name": "..."}, ...]."""
        try:
            devices = await _list_server_devices()
            return {"devices": devices}
        except Exception as e:
            _log.debug("webcam devices list failed: %s", e)
            return {"devices": []}

    @app.get("/api/webcam/stream")
    async def webcam_stream(device: int = Query(0, ge=0, le=4, description="Device index (0-4)")):
        """Stream MJPEG from server-attached camera. Requires ffmpeg on the server."""
        err = await _check_ffmpeg()
        if err:
            return Response(content=err, status_code=503, media_type="text/plain")
        err = await _check_device(device)
        if err:
            return Response(content=err, status_code=503, media_type="text/plain")
        return StreamingResponse(
            _stream_mjpeg(device),
            media_type=_MJPEG_CONTENT_TYPE,
        )
