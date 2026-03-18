# Orin AI Testbed — System Documentation

## Why This Exists

Manual SSH, manual Docker commands, manual model reloads — none of that scales when you're iterating on ML pipelines with live sensor input. This testbed gives you:

- **One-click container management** via Portainer (no SSH needed for 90% of ops)
- **Live system telemetry** via Heartbeat dashboard (GPU thermals, memory pressure, container health — in your browser)
- **Remote desktop** embedded directly in the monitoring dashboard (no separate VNC client)
- **Crash isolation** — you develop on your Mac, containers run on the Orin. If a model OOMs, your editor doesn't die.
- **Tailscale mesh** — no port forwarding, no firewall rules, no VPN configs. Just works from anywhere.

> **Bottom line**: You never need to SSH into the Orin for normal development. Push code, rebuild containers, monitor everything — all from Cursor on your Mac.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  YOUR MAC (Dev Machine)                                         │
│  Cursor + Claude Code + SSH + SCP                               │
│  Tailscale IP: (your Mac's Tailscale IP)                        │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐    │
│  │ Cursor IDE   │  │ Claude Code  │  │ Browser            │    │
│  │ (edit code)  │  │ (agent ops)  │  │ (dashboards)       │    │
│  └──────┬───────┘  └──────┬───────┘  └────────┬───────────┘    │
│         │                 │                    │                │
└─────────┼─────────────────┼────────────────────┼────────────────┘
          │ SSH/SCP         │ SSH/SCP            │ HTTP/WS
          │                 │                    │
     ─────┼─────── Tailscale Mesh ───────────────┼─────
          │                 │                    │
┌─────────┼─────────────────┼────────────────────┼────────────────┐
│  ORIN NANO (AI Testbed)   │                    │                │
│  Tailscale: 100.68.165.28 │                    │                │
│  Hostname: dog-station     │                    │                │
│                            │                    │                │
│  ┌────────────────────────────────────────────────────────┐     │
│  │                    Docker Engine                        │     │
│  │                                                        │     │
│  │  ┌─────────────┐ ┌──────────────┐ ┌────────────────┐  │     │
│  │  │ heartbeat   │ │ tanksense    │ │ portainer      │  │     │
│  │  │ :8888       │ │ :7860        │ │ :9443 (HTTPS)  │  │     │
│  │  │ System      │ │ HF Space     │ │ Container      │  │     │
│  │  │ monitor +   │ │ (tank model  │ │ management     │  │     │
│  │  │ VNC viewer  │ │  inference)  │ │ GUI            │  │     │
│  │  └─────────────┘ └──────────────┘ └────────────────┘  │     │
│  │  ┌─────────────┐                                      │     │
│  │  │ novnc-proxy │                                      │     │
│  │  │ :6080       │──── websockify ──── VNC :5901 (host) │     │
│  │  └─────────────┘                                      │     │
│  └────────────────────────────────────────────────────────┘     │
│                                                                 │
│  Host Services:                                                 │
│  • TigerVNC server on :5901 (desktop access)                    │
│  • CUDA 12.6 / cuDNN / TensorRT (JetPack 6)                    │
│  • NVIDIA Driver 540.4.0                                        │
│                                                                 │
│  Future Hardware:                                               │
│  • Intel RealSense D455i (USB) — color + depth + IMU            │
│  • Live test subject for capture                                │
└─────────────────────────────────────────────────────────────────┘
```

---

## Hardware

| Component | Spec |
|-----------|------|
| Board | NVIDIA Jetson Orin Nano Super Developer Kit |
| CPU | 6-core ARM Cortex-A78AE |
| GPU | 1024-core Ampere (CUDA 12.6) |
| RAM | 8 GB LPDDR5 (shared CPU/GPU) |
| Storage | 234 GB NVMe (~150 GB free) |
| JetPack | 6.0 (L4T R36.4.7) |
| OS | Ubuntu 22.04 |
| Network | Tailscale mesh, local WiFi |
| Planned sensor | Intel RealSense D455i (RGB + stereo depth + IMU) |

**Memory is shared** — GPU VRAM comes out of the same 8 GB. Watch the Heartbeat dashboard when loading models. If you cross ~6.5 GB total, OOM-killer will strike.

---

## Connections & Credentials

### SSH (for automation / Claude Code / Cursor remote)
```bash
# Direct
sshpass -p 'r00t' ssh dog@100.68.165.28

# SCP files
sshpass -p 'r00t' scp ./myfile dog@100.68.165.28:/home/dog/project/
```
| Field | Value |
|-------|-------|
| Host | `100.68.165.28` (Tailscale) |
| User | `dog` |
| Password | `r00t` |
| Port | 22 (default) |

### Portainer (Container Management GUI)
```
URL: https://100.68.165.28:9443
User: admin
Password: vaqfoz-komrip-2Fiqjy
```
**Value over CLI**: Visual container logs, one-click restart, resource graphs, image management, volume inspection — no SSH session needed. Great for when a container is misbehaving and you want to check logs + restart without context-switching from your editor.

### Heartbeat Dashboard (System Monitor + VNC)
```
URL: http://100.68.165.28:8888
```
No auth. Shows real-time: CPU per-core, GPU utilization/temp/power, memory, disk, thermals, network throughput, Docker container status with Start/Stop/Restart buttons, and an embedded VNC remote desktop viewer.

### VNC (Remote Desktop)
```
Direct VNC: 100.68.165.28:5901 (password: r00t)
Browser noVNC: http://100.68.165.28:6080/vnc.html
Embedded: Built into Heartbeat dashboard at :8888
```

### TankSense Demo (Current ML Model)
```
URL: http://100.68.165.28:7860
```
HuggingFace Space `inmert/tanksense-demo` running locally. This is the starting point for the model iteration work.

---

## Running Services

| Container | Port | Purpose | Restart Policy |
|-----------|------|---------|---------------|
| `heartbeat` | 8888 | System telemetry + VNC viewer | unless-stopped |
| `tanksense` | 7860 | ML inference (tank detection) | unless-stopped |
| `portainer` | 9443 | Docker management GUI | always |
| `novnc-proxy` | 6080 | Browser VNC via websockify | unless-stopped |

All containers auto-restart on reboot. VNC server (TigerVNC) runs on the host, not in Docker.

---

## Directory Structure (on Orin)

```
/home/dog/
├── heartbeat/
│   ├── app.py          # FastAPI + WebSocket monitor backend
│   ├── index.html      # Dashboard frontend (CPU/GPU/Docker/VNC)
│   └── Dockerfile
├── novnc-proxy/
│   └── Dockerfile      # websockify + noVNC static files
├── tanksense-demo/
│   ├── app.py          # FastAPI inference server
│   ├── index.html      # HF Space frontend
│   ├── requirements.txt
│   └── Dockerfile
└── (future: realsense-pipeline/)
```

---

## Development Workflow

### The golden loop (what you'll do 100 times):

```
1. Edit code in Cursor (on your Mac)
2. SCP to Orin:
   sshpass -p 'r00t' scp ./app.py dog@100.68.165.28:/home/dog/tanksense-demo/
3. Rebuild + redeploy:
   sshpass -p 'r00t' ssh dog@100.68.165.28 \
     'cd /home/dog/tanksense-demo && docker build -t tanksense-demo . && docker stop tanksense && docker rm tanksense && docker run -d --name tanksense --restart unless-stopped -p 7860:7860 tanksense-demo'
4. Test in browser: http://100.68.165.28:7860
5. Check GPU/memory in Heartbeat: http://100.68.165.28:8888
```

Or skip steps 2-3 and use **Portainer** to rebuild from the GUI.

### Why not develop directly on the Orin?

- 8 GB shared memory — your IDE + model + inference = OOM
- If a bad model load crashes the GPU driver, you lose your editor session
- Cursor + Claude Code on your Mac gives you AI-assisted development without competing for Orin resources
- The Orin is a **runtime target**, not a dev environment

---

## Project Mission

Build an iterative ML pipeline for:

1. **Capture**: Intel RealSense D455i provides RGB color + stereo depth + IMU data from live subjects
2. **Training**: Use captured data to train/fine-tune detection and segmentation models on the Orin's GPU
3. **Inference**: Real-time model serving via FastAPI containers
4. **Multi-view output**: Toggle between synthesized views:
   - Color (RGB passthrough)
   - Depth (from RealSense stereo)
   - Thermal (model-generated / sensor-fused)
   - Radar-style (model-generated)
   - LiDAR point cloud (from depth data)
5. **3D Model integration**: Existing 3D model to be incorporated into the pipeline

The TankSense demo is the **starting point** — it proves the container-based inference pattern works. The next phase replaces its static model with the RealSense-driven pipeline.

---

## Quick Reference Commands

```bash
# SSH into Orin
sshpass -p 'r00t' ssh dog@100.68.165.28

# Watch GPU in real time (on Orin)
tegrastats

# Check all containers
docker ps -a

# View container logs
docker logs -f tanksense

# Restart a container without SSH (use Heartbeat dashboard)
# Go to http://100.68.165.28:8888 → Docker section → click Restart

# Check disk space
df -h /

# Check memory pressure
free -h

# Kill a runaway process eating GPU memory
sudo kill -9 $(pgrep -f "python.*model")
```

---

## Gotchas

1. **Shared memory** — GPU and CPU share 8 GB. A 4 GB model + inference + system = tight. Monitor via Heartbeat.
2. **ARM64** — Not all Python packages have ARM wheels. If `pip install` fails, check for `aarch64` builds or build from source.
3. **No x86 Docker images** — Must use ARM64/aarch64 base images. `python:3.10-slim` works. NVIDIA-specific L4T images have inconsistent tags.
4. **Thermal throttling** — The Orin will throttle at ~85°C. Watch the thermal zones in Heartbeat during long training runs. Consider a fan or heatsink upgrade.
5. **VNC is display :1** — If VNC stops, restart with: `vncserver :1 -geometry 1920x1080 -depth 24`
6. **Portainer HTTPS** — Browser will warn about self-signed cert. Accept it. That's expected.
