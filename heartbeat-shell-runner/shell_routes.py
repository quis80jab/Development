"""
Heartbeat add-on: run/stop shell commands with path select and streaming output.
Merge this router and the dependencies into your existing FastAPI app.py.
"""
import asyncio
import json
import os
import uuid

from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import StreamingResponse

# Optional: restrict allowed working directories (e.g. ["/home/dog"]). Empty = allow any.
SHELL_CWD_ALLOW = []  # e.g. ["/home/dog"]

shell_router = APIRouter()

# id -> { "process": asyncio.SubprocessProcess, "queue": asyncio.Queue, "done": bool }
processes: dict[str, dict] = {}


def _check_cwd(cwd: str) -> str:
    """Resolve and optionally restrict cwd. Raises HTTPException if invalid."""
    try:
        resolved = os.path.realpath(cwd)
        if not os.path.isdir(resolved):
            raise HTTPException(status_code=400, detail=f"Not a directory: {cwd}")
        if SHELL_CWD_ALLOW:
            allowed = any(
                resolved == os.path.realpath(p) or resolved.startswith(os.path.realpath(p) + os.sep)
                for p in SHELL_CWD_ALLOW
            )
            if not allowed:
                raise HTTPException(status_code=403, detail=f"Path not allowed: {cwd}")
        return resolved
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=400, detail=str(e))


async def _stream_reader(process_id: str, stream):
    """Background: read process stdout into the shared queue."""
    entry = processes.get(process_id)
    if not entry:
        return
    queue = entry["queue"]
    try:
        while True:
            line = await stream.readline()
            if not line:
                break
            await queue.put(("out", line.decode("utf-8", errors="replace")))
    finally:
        entry["done"] = True
        await queue.put(("done", ""))


@shell_router.post("/run")
async def shell_run(cwd: str = Form("/home/dog"), command: str = Form("")):
    """Start a shell command in the given working directory. Returns process id for streaming/stop."""
    if not command or not command.strip():
        raise HTTPException(status_code=400, detail="command is required")
    resolved_cwd = _check_cwd(cwd)
    process_id = str(uuid.uuid4())
    queue: asyncio.Queue = asyncio.Queue()
    try:
        process = await asyncio.create_subprocess_shell(
            command.strip(),
            cwd=resolved_cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    processes[process_id] = {
        "process": process,
        "queue": queue,
        "done": False,
    }
    asyncio.create_task(_stream_reader(process_id, process.stdout))
    return {"id": process_id, "cwd": resolved_cwd, "command": command.strip()}


@shell_router.post("/stop")
async def shell_stop(id: str = Form(...)):
    """Send SIGTERM to a running command."""
    entry = processes.get(id)
    if not entry:
        raise HTTPException(status_code=404, detail="Process not found")
    try:
        entry["process"].terminate()
        await asyncio.wait_for(entry["process"].wait(), timeout=5.0)
    except asyncio.TimeoutError:
        entry["process"].kill()
    except Exception:
        pass
    entry["done"] = True
    return {"id": id, "status": "stopped"}


async def _sse_stream(process_id: str):
    """SSE generator: yield lines from the process queue until done."""
    entry = processes.get(process_id)
    if not entry:
        yield "data: " + json.dumps({"error": "Process not found"}) + "\n\n"
        return
    queue = entry["queue"]
    while not entry["done"] or not queue.empty():
        try:
            kind, line = await asyncio.wait_for(queue.get(), timeout=1.0)
            if kind == "done":
                break
            yield "data: " + json.dumps({"line": line}) + "\n\n"
        except asyncio.TimeoutError:
            yield ": keepalive\n\n"
    if process_id in processes:
        del processes[process_id]
    yield "data: " + json.dumps({"done": True}) + "\n\n"


@shell_router.get("/stream/{process_id}")
async def shell_stream(process_id: str):
    """Server-Sent Events stream of command output. Connect after POST /run."""
    return StreamingResponse(
        _sse_stream(process_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@shell_router.get("/paths")
async def shell_paths(path: str = "/home/dog", q: str | None = None):
    """List directory entries under `path`, optionally filtered by substring `q`. For path search/select in the UI."""
    resolved = _check_cwd(path)
    try:
        entries = []
        with os.scandir(resolved) as it:
            for e in it:
                if e.name.startswith(".") and (not q or "." not in q):
                    continue
                try:
                    is_dir = e.is_dir()
                except OSError:
                    continue
                name = e.name + ("/" if is_dir else "")
                if q and q.strip().lower() not in name.lower():
                    continue
                entries.append({"name": name, "dir": is_dir})
        entries.sort(key=lambda x: (not x["dir"], x["name"].lower()))
        return {"path": resolved, "entries": entries[:200]}
    except OSError as e:
        raise HTTPException(status_code=400, detail=str(e))
