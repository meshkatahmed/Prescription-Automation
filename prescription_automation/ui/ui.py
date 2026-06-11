from __future__ import annotations

from pathlib import Path


def get_ui_html() -> str:
    html_path = Path(__file__).resolve().parents[2] / "ui.html"
    if not html_path.exists():
        raise FileNotFoundError(
            f"UI HTML file not found at {html_path}. Ensure ui.html exists in the project root."
        )
    return html_path.read_text(encoding="utf-8")
