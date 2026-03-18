import asyncio, json, time, subprocess, os, re, signal
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from pathlib import Path
from shell_routes import shell_router

app = FastAPI(title="Heartbeat")
app.include_router(shell_router, prefix="/api/shell", tags=["shell"])


def get_cpu():
    with open("/proc/stat") as f:
        lines = f.readlines()
    cpu = lines[0].split()
    total = sum(int(x) for x in cpu[1:])
    idle = int(cpu[4])
    cores = []
    for line in lines[1:]:
        if not line.startswith("cpu"):
            break
        parts = line.split()
        ct = sum(int(x) for x in parts[1:])
        ci = int(parts[4])
        cores.append({"total": ct, "idle": ci})
    with open("/proc/loadavg") as f:
        load = f.read().split()[:3]
    freqs = []
    for i in range(os.cpu_count() or 6):
        try:
            with open(f"/sys/devices/system/cpu/cpu{i}/cpufreq/scaling_cur_freq") as f:
                freqs.append(int(f.read().strip()) / 1000)
        except:
            freqs.append(0)
    return {"total": total, "idle": idle, "cores": cores, "load": load, "freqs_mhz": freqs}


def get_memory():
    with open("/proc/meminfo") as f:
        info = {}
        for line in f:
            parts = line.split()
            info[parts[0].rstrip(":")] = int(parts[1])
    total = info.get("MemTotal", 0)
    avail = info.get("MemAvailable", 0)
    swap_total = info.get("SwapTotal", 0)
    swap_free = info.get("SwapFree", 0)
    return {
        "total_mb": total // 1024,
        "used_mb": (total - avail) // 1024,
        "swap_total_mb": swap_total // 1024,
        "swap_used_mb": (swap_total - swap_free) // 1024,
    }


def get_gpu():
    try:
        out = subprocess.check_output(
            ["tegrastats", "--interval", "100", "--count", "1"],
            timeout=3, stderr=subprocess.DEVNULL,
        ).decode()
        gpu_match = re.search(r"GR3D_FREQ\s+(\d+)%", out)
        gpu_pct = int(gpu_match.group(1)) if gpu_match else 0
        temp_match = re.search(r"GPU@([\d.]+)C", out)
        gpu_temp = float(temp_match.group(1)) if temp_match else None
        pwr_match = re.search(r"VDD_GPU_SOC\s+(\d+)mW", out)
        gpu_power_mw = int(pwr_match.group(1)) if pwr_match else None
        total_pwr = re.search(r"VDD_IN\s+(\d+)mW", out)
        total_power_mw = int(total_pwr.group(1)) if total_pwr else None
        return {
            "utilization_pct": gpu_pct,
            "temp_c": gpu_temp,
            "power_mw": gpu_power_mw,
            "total_power_mw": total_power_mw,
            "raw": out.strip(),
        }
    except Exception as e:
        return {"utilization_pct": 0, "temp_c": None, "error": str(e)}


def get_thermal():
    temps = {}
    thermal_base = Path("/sys/class/thermal/")
    for tz in sorted(thermal_base.glob("thermal_zone*")):
        try:
            name = (tz / "type").read_text().strip()
            temp = int((tz / "temp").read_text().strip()) / 1000
            temps[name] = temp
        except:
            pass
    return temps


def get_network():
    with open("/proc/net/dev") as f:
        lines = f.readlines()[2:]
    interfaces = {}
    for line in lines:
        parts = line.split()
        iface = parts[0].rstrip(":")
        if iface == "lo":
            continue
        interfaces[iface] = {
            "rx_bytes": int(parts[1]),
            "tx_bytes": int(parts[9]),
            "rx_packets": int(parts[2]),
            "tx_packets": int(parts[10]),
        }
    return interfaces


def get_disk():
    result = subprocess.check_output(["df", "-B1", "/"], timeout=3).decode().split("\n")[1].split()
    return {
        "total_gb": round(int(result[1]) / 1e9, 1),
        "used_gb": round(int(result[2]) / 1e9, 1),
        "avail_gb": round(int(result[3]) / 1e9, 1),
        "pct": result[4],
    }


def get_docker():
    try:
        out = subprocess.check_output(
            ["docker", "ps", "-a", "--format", "{{.Names}}|{{.Image}}|{{.Status}}|{{.Ports}}"],
            timeout=5, stderr=subprocess.DEVNULL,
        ).decode().strip()
        containers = []
        for line in out.split("\n"):
            if not line:
                continue
            parts = line.split("|")
            containers.append({"name": parts[0], "image": parts[1], "status": parts[2], "ports": parts[3]})
        return containers
    except:
        return []


def get_uptime():
    with open("/proc/uptime") as f:
        secs = float(f.read().split()[0])
    d, r = divmod(int(secs), 86400)
    h, r = divmod(r, 3600)
    m, s = divmod(r, 60)
    return f"{d}d {h}h {m}m {s}s"


def _host_exec(cmd: str, timeout: int = 15) -> str:
    """Execute a command on the host via nsenter (requires --pid=host on container)."""
    return subprocess.check_output(
        ["nsenter", "-t", "1", "-m", "-u", "-i", "-n", "--", "sh", "-c", cmd],
        timeout=timeout, stderr=subprocess.STDOUT,
    ).decode().strip()


@app.get("/", response_class=HTMLResponse)
async def index():
    return Path("/app/index.html").read_text()


@app.get("/api/snapshot")
async def snapshot():
    return {
        "ts": time.time(),
        "uptime": get_uptime(),
        "cpu": get_cpu(),
        "memory": get_memory(),
        "gpu": get_gpu(),
        "thermal": get_thermal(),
        "network": get_network(),
        "disk": get_disk(),
        "docker": get_docker(),
    }


@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    await websocket.accept()
    prev_cpu = None
    prev_net = None
    try:
        while True:
            data = {
                "ts": time.time(),
                "uptime": get_uptime(),
                "cpu": get_cpu(),
                "memory": get_memory(),
                "gpu": get_gpu(),
                "thermal": get_thermal(),
                "network": get_network(),
                "disk": get_disk(),
                "docker": get_docker(),
            }
            await websocket.send_json(data)
            await asyncio.sleep(1.5)
    except WebSocketDisconnect:
        pass


@app.post("/api/docker/{action}/{container}")
async def docker_control(action: str, container: str):
    if action not in ("start", "stop", "restart"):
        return {"error": "invalid action"}
    try:
        subprocess.check_output(["docker", action, container], timeout=30, stderr=subprocess.STDOUT)
        return {"ok": True, "action": action, "container": container}
    except subprocess.CalledProcessError as e:
        return {"error": e.output.decode()}


def _host_exec_bg(cmd: str) -> None:
    """Fire-and-forget a command on the host via nsenter (does not wait)."""
    subprocess.Popen(
        ["nsenter", "-t", "1", "-m", "-u", "-i", "-n", "--", "sh", "-c", cmd],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        start_new_session=True,
    )


def _vnc_running() -> bool:
    """Check if Xtigervnc is running on the host for user dog."""
    try:
        _host_exec("pgrep -u dog Xtigervnc", timeout=5)
        return True
    except Exception:
        return False


@app.post("/api/vnc-server/{action}")
async def vnc_server_control(action: str):
    """Start / stop / reboot the host TigerVNC server on display :1 via systemd."""
    if action not in ("start", "stop", "reboot"):
        return {"error": "invalid action"}

    try:
        if action == "stop":
            _host_exec("systemctl stop vncserver.service vnc-session.service", timeout=15)
            return {"ok": True, "action": "stop", "output": "VNC server stopped"}

        if action == "reboot":
            _host_exec("systemctl stop vncserver.service vnc-session.service", timeout=15)
            await asyncio.sleep(1)

        # start / reboot
        _host_exec("systemctl start vncserver.service", timeout=15)
        await asyncio.sleep(2)
        _host_exec_bg("systemctl start vnc-session.service")

        for _ in range(8):
            await asyncio.sleep(1)
            if _vnc_running():
                return {"ok": True, "action": action, "output": "VNC server running on :1"}
        return {"ok": True, "action": action, "output": "VNC server start issued (may still be initializing)"}
    except subprocess.CalledProcessError as e:
        return {"error": e.output.decode().strip()}
    except Exception as e:
        return {"error": str(e)}
