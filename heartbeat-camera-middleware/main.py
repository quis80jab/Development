import asyncio
import os
import time
from contextlib import asynccontextmanager
from typing import Dict, Optional

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


CAM_BASE_URL = os.environ.get("CAM_BASE_URL", "http://127.0.0.1:8890").rstrip("/")

STREAMS_CONFIG = {
    "rs_color": {
        "label": "RealSense D455 — Color",
        "snapshot_url": f"{CAM_BASE_URL}/snapshot/realsense/color",
    },
    "rs_depth": {
        "label": "RealSense D455 — Depth",
        "snapshot_url": f"{CAM_BASE_URL}/snapshot/realsense/depth",
    },
    "flir": {
        "label": "Teledyne FLIR Blackfly",
        "snapshot_url": f"{CAM_BASE_URL}/snapshot/blackfly",
    },
}

POLL_FPS = float(os.environ.get("CAM_MW_POLL_FPS", "5.0"))
POLL_INTERVAL = 1.0 / POLL_FPS if POLL_FPS > 0 else 0.2


class StreamState:
    def __init__(self, stream_id: str, label: str, snapshot_url: str) -> None:
        self.id = stream_id
        self.label = label
        self.snapshot_url = snapshot_url
        self.latest_frame: Optional[bytes] = None
        self.latest_ts: Optional[float] = None
        self.ok: bool = False
        self.error: str = ""


streams: Dict[str, StreamState] = {
    sid: StreamState(sid, cfg["label"], cfg["snapshot_url"])
    for sid, cfg in STREAMS_CONFIG.items()
}

active_stream_id: str = "rs_color"
shutdown_event = asyncio.Event()

templates = Jinja2Templates(
    directory=os.path.join(os.path.dirname(__file__), "templates")
)


async def poll_stream(state: StreamState) -> None:
    async with httpx.AsyncClient(timeout=httpx.Timeout(3.0, read=3.0)) as client:
        while not shutdown_event.is_set():
            try:
                resp = await client.get(state.snapshot_url)
                if resp.status_code == 200 and resp.headers.get(
                    "content-type", ""
                ).startswith("image/"):
                    state.latest_frame = resp.content
                    state.latest_ts = time.time()
                    state.ok = True
                    state.error = ""
                else:
                    state.ok = False
                    state.error = f"Bad status {resp.status_code}"
            except Exception as e:
                state.ok = False
                state.error = str(e)

            await asyncio.sleep(POLL_INTERVAL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    tasks = [asyncio.create_task(poll_stream(s)) for s in streams.values()]
    yield
    shutdown_event.set()
    for t in tasks:
        t.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)


app = FastAPI(title="Heartbeat Camera Middleware", lifespan=lifespan)


@app.get("/healthz")
async def healthz() -> Dict[str, str]:
    return {"status": "ok", "active_stream": active_stream_id}


@app.get("/api/streams")
async def get_streams() -> Dict[str, object]:
    data = []
    for sid, state in streams.items():
        data.append(
            {
                "id": sid,
                "label": state.label,
                "ok": state.ok,
                "last_seen_ts": state.latest_ts,
                "error": state.error,
                "active": sid == active_stream_id,
            }
        )
    return {"streams": data}


@app.post("/api/streams/select")
async def select_stream(payload: Dict[str, str]) -> Dict[str, object]:
    global active_stream_id
    sid = payload.get("id")
    if sid not in streams:
        raise HTTPException(status_code=400, detail="Unknown stream id")
    active_stream_id = sid
    return {"active_stream": sid}


@app.get("/api/frame")
async def get_frame() -> Response:
    state = streams.get(active_stream_id)
    if state is None:
        raise HTTPException(status_code=500, detail="Active stream missing")
    if not state.latest_frame:
        raise HTTPException(status_code=503, detail="No frame available")
    return Response(
        content=state.latest_frame,
        media_type="image/jpeg",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Access-Control-Allow-Origin": "*",
        },
    )


@app.get("/webcam", response_class=HTMLResponse)
async def webcam_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "webcam.html",
        {
            "request": request,
        },
    )


@app.get("/tanksense", response_class=HTMLResponse)
async def tanksense_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "tanksense.html",
        {
            "request": request,
        },
    )


static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers={"Access-Control-Allow-Origin": "*"},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.environ.get("CAM_MW_PORT", "8891")),
        reload=False,
    )

