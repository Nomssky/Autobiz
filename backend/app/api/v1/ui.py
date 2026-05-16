"""UI router — serves HTML dashboard for WebView TUI."""

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from starlette.staticfiles import StaticFiles

UI_DIR = Path(__file__).resolve().parents[3] / "ui"

router = APIRouter(tags=["ui"])


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    path = UI_DIR / "dashboard.html"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return HTMLResponse(path.read_text(encoding="utf-8"))


@router.get("/agents/{name}", response_class=HTMLResponse)
def agent_detail(name: str):
    path = UI_DIR / "detail.html"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Detail page not found")
    html = path.read_text(encoding="utf-8")
    html = html.replace("{{AGENT_NAME}}", name)
    return HTMLResponse(html)


@router.get("/static/{filename}")
def static_file(filename: str):
    path = UI_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path)
