from __future__ import annotations

import asyncio
import os
import tempfile
import uuid
import webbrowser
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from pathlib import Path
from threading import Thread
from typing import Any, Dict

import uvicorn
from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from docdiff.differ import Differ
from docdiff.embedder import Embedder
from docdiff.html_generator import HtmlGenerator
from docdiff.matcher import Matcher
from docdiff.parser import parse_docx


# In-memory cache for job results
jobs: Dict[str, Any] = {}
executor = ThreadPoolExecutor(max_workers=2)

def _do_compare(job_id: str, old_path: Path, new_path: Path, threshold: float, device: str | None) -> None:
    """Run comparison in background thread."""
    try:
        embedder = Embedder(device=device)
        matcher = Matcher(embedder, threshold=threshold)
        differ = Differ()
        html_generator = HtmlGenerator(differ)

        blocks_old = parse_docx(old_path)
        blocks_new = parse_docx(new_path)
        match_result = matcher.match(blocks_old, blocks_new)
        html = html_generator.generate(match_result)

        jobs[job_id] = {
            "status": "done",
            "html": html,
            "error": None,
        }
    except Exception as e:
        jobs[job_id] = {
            "status": "error",
            "html": None,
            "error": str(e),
        }

_TEMPLATES_DIR = Path(__file__).parent / "templates"

def _read_index_html() -> str:
    path = _TEMPLATES_DIR / "index.html"
    return path.read_text(encoding="utf-8")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan manager."""
    yield
    executor.shutdown(wait=False)

app = FastAPI(title="DocDiff", lifespan=lifespan)
_static_dir = Path(__file__).parent / "static"
if _static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> Any:
    return HTMLResponse(content=_read_index_html())


@app.post("/compare")
async def compare(
    old_file: UploadFile = File(...),
    new_file: UploadFile = File(...),
    threshold: float = Form(0.75),
    device: str = Form("cpu"),
) -> Any:
    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "processing", "html": None, "error": None}

    # Save uploaded files to temp dir
    temp_dir = Path(tempfile.gettempdir()) / "docdiff" / job_id
    temp_dir.mkdir(parents=True, exist_ok=True)
    old_path = temp_dir / old_file.filename
    new_path = temp_dir / new_file.filename

    with open(old_path, "wb") as f:
        f.write(await old_file.read())
    with open(new_path, "wb") as f:
        f.write(await new_file.read())

    # Run comparison in thread pool
    loop = asyncio.get_event_loop()
    loop.run_in_executor(
        executor,
        _do_compare,
        job_id,
        old_path,
        new_path,
        threshold,
        device,
    )

    return {"job_id": job_id, "status": "processing"}


@app.get("/result/{job_id}")
async def get_result(job_id: str) -> Any:
    job = jobs.get(job_id)
    if not job:
        return {"status": "not_found"}
    return job


@app.get("/result/{job_id}/html", response_class=HTMLResponse)
async def get_result_html(job_id: str) -> Any:
    job = jobs.get(job_id)
    if not job or job["status"] != "done":
        return HTMLResponse("<h1>Not ready</h1>", status_code=202)
    return HTMLResponse(job["html"])


def run_server(host: str = "127.0.0.1", port: int = 8000, open_browser: bool = True) -> None:
    """Run the web server."""
    if open_browser:
        url = f"http://{host}:{port}"
        Thread(target=lambda: (_wait_for_server(host, port), webbrowser.open(url)), daemon=True).start()
    uvicorn.run(app, host=host, port=port, log_level="warning")


def _wait_for_server(host: str, port: int, timeout: float = 10.0) -> None:
    import socket
    import time
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), timeout=1):
                return
        except OSError:
            time.sleep(0.2)
