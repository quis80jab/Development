"""
Heartbeat add-on: run/stop shell commands on the HOST via nsenter, with path select and streaming output.
All filesystem operations and command execution happen on the host, not inside the container.
Requires: --privileged --pid=host on the container.
"""
import asyncio
import json
import subprocess
import uuid

from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import StreamingResponse

# Optional: restrict allowed working directories (e.g. ["/home/dog"]). Empty = allow any.
SHELL_CWD_ALLOW = []  # e.g. ["/home/dog"]

shell_router = APIRouter()

# id -> { "process": asyncio.SubprocessProcess, "queue": asyncio.Queue, "done": bool }
processes: dict[str, dict] = {}


def _host_cmd(cmd: str, timeout: int = 10) -> str:
    """Run a command on the host via nsenter and return stdout."""
    return subprocess.check_output(
        ["nsenter", "-t", "1", "-m", "-u", "-i", "-n", "--", "sh", "-c", cmd],
        timeout=timeout, stderr=subprocess.STDOUT,
    ).decode().strip()


def _check_cwd(cwd: str) -> str:
    """Validate that cwd exists as a directory on the HOST. Raises HTTPException if invalid."""
    try:
        # Resolve and check on the host filesystem
        resolved = _host_cmd(f'realpath "{cwd}" 2>/dev/null && test -d "{cwd}" && echo OK')
        lines = resolved.split("\n")
        if len(lines) < 2 or lines[-1] != "OK":
            raise HTTPException(status_code=400, detail=f"Not a directory on host: {cwd}")
        resolved_path = lines[0]
        if SHELL_CWD_ALLOW:
            allowed = any(
                resolved_path == p or resolved_path.startswith(p + "/")
                for p in SHELL_CWD_ALLOW
            )
            if not allowed:
                raise HTTPException(status_code=403, detail=f"Path not allowed: {cwd}")
        return resolved_path
    except HTTPException:
        raise
    except Exception as e:
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
    """Start a shell command on the HOST in the given working directory. Returns process id for streaming/stop."""
    if not command or not command.strip():
        raise HTTPException(status_code=400, detail="command is required")
    resolved_cwd = _check_cwd(cwd)
    process_id = str(uuid.uuid4())
    queue: asyncio.Queue = asyncio.Queue()
    # Run the command on the host via nsenter
    escaped_cmd = command.strip().replace("'", "'\\''")
    nsenter_cmd = f"nsenter -t 1 -m -u -i -n -- sh -c 'cd \"{resolved_cwd}\" && {escaped_cmd}'"
    try:
        process = await asyncio.create_subprocess_shell(
            nsenter_cmd,
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
    """List directory entries on the HOST under `path`, optionally filtered by substring `q`."""
    resolved = _check_cwd(path)
    try:
        # List directories and files on the host via nsenter
        # Output format: type\tname (d for dir, f for file)
        filter_part = ""
        if q and q.strip():
            filter_part = f" | grep -i '{q.strip()}'"
        raw = _host_cmd(
            f'cd "{resolved}" && '
            f'for f in $(ls -1A 2>/dev/null); do '
            f'  if [ -d "$f" ]; then echo "d\t$f"; else echo "f\t$f"; fi; '
            f'done{filter_part}',
            timeout=10,
        )
        entries = []
        for line in raw.split("\n"):
            if not line or "\t" not in line:
                continue
            kind, name = line.split("\t", 1)
            if name.startswith(".") and (not q or "." not in q):
                continue
            is_dir = kind == "d"
            entries.append({"name": name + ("/" if is_dir else ""), "dir": is_dir})
        entries.sort(key=lambda x: (not x["dir"], x["name"].lower()))
        return {"path": resolved, "entries": entries[:200]}
    except subprocess.CalledProcessError:
        # Empty directory or no matches
        return {"path": resolved, "entries": []}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
