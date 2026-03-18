## Heartbeat Camera Middleware Deployment

This service exposes the existing Heartbeat camera server (RealSense D455 color/depth and FLIR Blackfly) as a webcam-like browser feed for HuggingFace projects running on the same Orin.

### 1. Install dependencies on the Orin

From the Orin host (same machine that runs `camera_server.py` and the `heartbeat` container):

```bash
cd ~/ARACHNID/Development/heartbeat-camera-middleware
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

Requirements:

- `camera_server.py` already running on the host and listening on `http://127.0.0.1:8890`
- RealSense D455i and FLIR Blackfly physically connected and working with Heartbeat

### 2. Run the middleware service

For a quick manual run:

```bash
cd ~/ARACHNID/Development/heartbeat-camera-middleware
. .venv/bin/activate
CAM_MW_PORT=8891 uvicorn main:app --host 0.0.0.0 --port 8891
```

Environment variables:

- `CAM_MW_PORT` (optional): Port to expose (default `8891`).
- `CAM_MW_POLL_FPS` (optional): Snapshot polling rate from `camera_server.py` (default `5.0` FPS).

### 3. Systemd service (recommended)

Create `/etc/systemd/system/heartbeat-camera-middleware.service` on the Orin:

```ini
[Unit]
Description=Heartbeat Camera Middleware (webcam bridge)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=dog
WorkingDirectory=/home/dog/ARACHNID/Development/heartbeat-camera-middleware
Environment=CAM_MW_PORT=8891
Environment=CAM_MW_POLL_FPS=5.0
ExecStart=/home/dog/ARACHNID/Development/heartbeat-camera-middleware/.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8891
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Then:

```bash
sudo systemctl daemon-reload
sudo systemctl enable heartbeat-camera-middleware
sudo systemctl start heartbeat-camera-middleware
sudo systemctl status heartbeat-camera-middleware
```

The service will be available at:

- `http://<orin-ip>:8891/healthz`
- `http://<orin-ip>:8891/webcam`

### 4. Using from a HuggingFace Space on the same Orin

- **Browser-side:** load `http://127.0.0.1:8891/webcam` in an iframe, or copy the JS snippet exposed there.
- Access the `MediaStream`:

```js
// After /webcam has initialized:
const stream = window.heartbeatCamera.getMediaStream();
const video = document.querySelector("video");
video.srcObject = stream;
video.play();
```

- Switch between RealSense color, RealSense depth, and FLIR from the UI or:

```js
window.heartbeatCamera.selectStream("rs_color");  // or "rs_depth", "flir"
```

### 5. Optional: server-side frame access

If your HuggingFace backend (Python) needs raw frames:

- Call `GET http://127.0.0.1:8891/api/frame` to retrieve the latest JPEG for the active stream.
- Use `GET /api/streams` and `POST /api/streams/select` to inspect and change the active feed.

### 6. Dummy “webcam device” for HuggingFace (v4l2loopback)

If your HuggingFace code expects a *real* webcam device (e.g. `cv2.VideoCapture(0)` or `/dev/video10`), use a virtual V4L2 loopback device.

#### 6.1 Create a virtual webcam device

Install `v4l2loopback` (method depends on your Orin image). Then create a device:

```bash
# Example: create /dev/video10 with a friendly name
sudo modprobe v4l2loopback video_nr=10 card_label="HeartbeatCam" exclusive_caps=1
```

Verify:

```bash
v4l2-ctl --list-devices | grep -A2 HeartbeatCam
ls -l /dev/video10
```

#### 6.2 Run the bridge (writes frames into /dev/video10)

This bridge pulls JPEG frames from the middleware and pushes raw frames into the loopback device using `ffmpeg`.

```bash
cd ~/ARACHNID/Development/heartbeat-camera-middleware
. .venv/bin/activate

# Ensure ffmpeg is installed on the host
ffmpeg -version

python3 v4l2_webcam_bridge.py \
  --source "http://127.0.0.1:8891/api/frame" \
  --device "/dev/video10" \
  --size 640x480 \
  --fps 15 \
  --poll-fps 10
```

Now HuggingFace (or any app) can open it like a normal webcam:

```python
import cv2

cap = cv2.VideoCapture("/dev/video10")
ok, frame = cap.read()
print(ok, frame.shape if ok else None)
cap.release()
```

#### 6.3 Switching feeds

The bridge writes whatever the middleware’s **active stream** is. Switch active stream via:

- The middleware UI: `http://127.0.0.1:8891/webcam`
- Or API:

```bash
curl -X POST http://127.0.0.1:8891/api/streams/select \
  -H 'Content-Type: application/json' \
  -d '{"id":"flir"}'
```

