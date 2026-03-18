# Heartbeat Shell Runner — Add-on

Adds a **run / stop shell commands** feature to the Heartbeat app, with **path select, write, and search**.

Merge the backend routes into your existing `app.py` and the frontend section into `index.html` (see below). Redeploy the heartbeat container after merging.

## Features

- **Path**: Type a working directory path, or use **Search** to list/filter directories and pick one.
- **Command**: Type any shell command or pick a preset (e.g. `ls -la`, `docker ps`).
- **Run**: Start the command in the chosen path; output streams in the UI.
- **Stop**: Send SIGTERM to the running process.

## Security

Runs arbitrary shell on the Orin. Intended for trusted dev use on the Tailscale mesh only. Optional: restrict `SHELL_CWD_ALLOW` in the backend to a list of allowed base paths (e.g. `/home/dog`).

## Deploy to Orin (one command)

From your Mac (with Tailscale so the Orin is reachable):

```bash
cd heartbeat-shell-runner
./deploy-to-orin.sh
```

Install `sshpass` for non-interactive password auth: `brew install sshpass`. Otherwise you’ll be prompted for the Orin password.

## Merge instructions (manual)

1. **Backend** (in `app.py`):
   - Import: `from shell_routes import shell_router` (or paste the router code into `app.py` and ensure `processes` is at module level).
   - Mount: `app.include_router(shell_router, prefix="/api/shell", tags=["shell"])`
2. **Frontend**: Insert the full contents of `shell_runner_section.html` into your dashboard (one new card/section). It is self-contained (HTML + CSS + JS).
3. Rebuild and redeploy the heartbeat container.

## Files

| File | Purpose |
|------|---------|
| `shell_routes.py` | FastAPI routes: run, stop, stream (SSE), path search |
| `shell_runner_section.html` | HTML + CSS + JS for path input (with search), command input, run/stop, streaming output |
