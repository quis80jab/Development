# Arachnid — Orin AI Testbed

Development documentation for the NVIDIA Jetson Orin Nano AI testbed.

## Value for the team

With these docs and the Cursor agent prompt, you never SSH manually, never guess memory headroom, and never rebuild blind. **Cursor + `CURSOR-AGENT-PROMPT.md`** = the agent knows the hardware limits, the deploy pattern, and where to look when things break.

## Contents

| File | Purpose |
|------|---------|
| `ORIN-TESTBED-DOCS.md` | Complete system documentation — architecture, credentials, hardware, workflows, gotchas |
| `CURSOR-AGENT-PROMPT.md` | Paste into Cursor `.cursorrules` to give the AI agent full context on the testbed |
| `orin-testbed-docs.pdf` | PDF version of the system docs for sharing / offline reference |
| `heartbeat-shell-runner/` | Add-on: run/stop shell commands from Heartbeat with path select, write, and search |

## Quick Access

| Service | URL |
|---------|-----|
| Heartbeat (monitor + VNC) | http://100.68.165.28:8888 |
| Portainer (containers) | https://100.68.165.28:9443 |
| TankSense (model demo) | http://100.68.165.28:7860 |
| noVNC (remote desktop) | http://100.68.165.28:6080/vnc.html |

## Getting Started

1. Read `ORIN-TESTBED-DOCS.md` for full system understanding
2. Copy `CURSOR-AGENT-PROMPT.md` content into your Cursor `.cursorrules` file
3. Open Heartbeat dashboard in your browser to verify the Orin is online
4. Start developing — edit locally, SCP + rebuild on Orin

## Team

- **Ben** — Infrastructure, system setup
- **Priyan** — ML pipeline development, model iteration
