"""
Module asset loader. Use from module.py to load HTML, CSS, JS from sibling files.
"""

from pathlib import Path
from typing import Tuple


def load_assets(module_file: str) -> Tuple[str, str, str]:
    """
    Load index.html, style.css, script.js from the same folder as module_file.
    Use from module.py: html, css, js = load_assets(__file__)

    Returns:
        (inner_html, css, js) - file contents or empty strings if missing
    """
    folder = Path(module_file).resolve().parent

    def _read(name: str) -> str:
        p = folder / name
        if p.is_file():
            try:
                return p.read_text(encoding="utf-8").strip()
            except (OSError, UnicodeDecodeError):
                pass
        return ""

    return (
        _read("index.html"),
        _read("style.css"),
        _read("script.js"),
    )
