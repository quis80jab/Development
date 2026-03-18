#!/usr/bin/env python3
"""
Camera streaming server for Heartbeat dashboard.
Captures from Intel RealSense D455 and FLIR Blackfly S BFS-U3-32S4M,
serves MJPEG streams over HTTP.

Runs on the HOST (not in Docker) as a systemd service.
Dependencies: pyrealsense2, PyGObject (gi.repository.Aravis), opencv-python, numpy
"""

import threading
import time
import signal
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn

import cv2
import numpy as np

# ── Globals ──────────────────────────────────────────────────────────────────
PORT = 8890
REALSENSE_FPS = 15
BLACKFLY_FPS = 10
JPEG_QUALITY = 70

# Latest frames (written by capture threads, read by HTTP handlers)
latest_frames = {
    "realsense_color": None,
    "realsense_depth": None,
    "blackfly": None,
}
frame_locks = {k: threading.Lock() for k in latest_frames}
camera_status = {
    "realsense": {"ok": False, "error": ""},
    "blackfly": {"ok": False, "error": ""},
}
shutdown_event = threading.Event()


# ── RealSense capture thread ────────────────────────────────────────────────
def realsense_capture():
    """Capture color + depth from Intel RealSense D455."""
    import pyrealsense2 as rs

    while not shutdown_event.is_set():
        pipeline = None
        try:
            pipeline = rs.pipeline()
            config = rs.config()
            config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, REALSENSE_FPS)
            config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, REALSENSE_FPS)
            pipeline.start(config)
            camera_status["realsense"]["ok"] = True
            camera_status["realsense"]["error"] = ""

            # Depth colorizer
            colorizer = rs.colorizer()
            colorizer.set_option(rs.option.color_scheme, 2)  # white-to-black

            while not shutdown_event.is_set():
                frames = pipeline.wait_for_frames(5000)
                color_frame = frames.get_color_frame()
                depth_frame = frames.get_depth_frame()

                if color_frame:
                    color_img = np.asanyarray(color_frame.get_data())
                    _, jpeg = cv2.imencode(".jpg", color_img, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
                    with frame_locks["realsense_color"]:
                        latest_frames["realsense_color"] = jpeg.tobytes()

                if depth_frame:
                    depth_color = np.asanyarray(colorizer.colorize(depth_frame).get_data())
                    _, jpeg = cv2.imencode(".jpg", depth_color, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
                    with frame_locks["realsense_depth"]:
                        latest_frames["realsense_depth"] = jpeg.tobytes()

        except Exception as e:
            camera_status["realsense"]["ok"] = False
            camera_status["realsense"]["error"] = str(e)
        finally:
            if pipeline:
                try:
                    pipeline.stop()
                except Exception:
                    pass

        if not shutdown_event.is_set():
            time.sleep(3)  # reconnect delay


# ── Blackfly capture thread ─────────────────────────────────────────────────
def blackfly_capture():
    """Capture from FLIR Blackfly S via Aravis (GenICam / USB3 Vision)."""
    import gi
    gi.require_version("Aravis", "0.8")
    from gi.repository import Aravis

    CAMERA_ID = None  # auto-detect first FLIR camera

    while not shutdown_event.is_set():
        cam = None
        stream = None
        try:
            # Find camera
            Aravis.update_device_list()
            n_devices = Aravis.get_n_devices()
            for i in range(n_devices):
                dev_id = Aravis.get_device_id(i)
                if "FLIR" in dev_id or "1E10" in dev_id:
                    CAMERA_ID = dev_id
                    break

            if not CAMERA_ID:
                raise RuntimeError("No FLIR camera found")

            cam = Aravis.Camera.new(CAMERA_ID)
            cam.set_pixel_format(Aravis.PIXEL_FORMAT_MONO_8)

            # Use a smaller ROI for lower bandwidth / higher FPS
            cam.set_region(0, 0, 1024, 768)
            cam.set_frame_rate(BLACKFLY_FPS)

            w, h = 1024, 768
            payload = cam.get_payload()

            stream = cam.create_stream(None, None)
            for _ in range(3):
                stream.push_buffer(Aravis.Buffer.new_allocate(payload))

            cam.start_acquisition()
            camera_status["blackfly"]["ok"] = True
            camera_status["blackfly"]["error"] = ""

            while not shutdown_event.is_set():
                buf = stream.timeout_pop_buffer(2000000)  # 2 sec
                if buf is None:
                    continue
                if buf.get_status() != Aravis.BufferStatus.SUCCESS:
                    stream.push_buffer(buf)
                    continue

                data = buf.get_data()
                arr = np.frombuffer(bytes(data), dtype=np.uint8).reshape(h, w)
                _, jpeg = cv2.imencode(".jpg", arr, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
                with frame_locks["blackfly"]:
                    latest_frames["blackfly"] = jpeg.tobytes()

                stream.push_buffer(buf)

        except Exception as e:
            camera_status["blackfly"]["ok"] = False
            camera_status["blackfly"]["error"] = str(e)
        finally:
            if cam:
                try:
                    cam.stop_acquisition()
                except Exception:
                    pass
            stream = None
            cam = None

        if not shutdown_event.is_set():
            time.sleep(3)  # reconnect delay


# ── HTTP Server ──────────────────────────────────────────────────────────────
class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


class CameraHandler(BaseHTTPRequestHandler):
    """Serves MJPEG streams and status JSON."""

    def log_message(self, fmt, *args):
        pass  # suppress noisy logs

    def do_GET(self):
        path = self.path.rstrip("/")

        if path == "/status":
            self._send_json({
                "cameras": camera_status,
                "streams": {
                    "realsense_color": latest_frames["realsense_color"] is not None,
                    "realsense_depth": latest_frames["realsense_depth"] is not None,
                    "blackfly": latest_frames["blackfly"] is not None,
                },
            })

        elif path == "/realsense/color":
            self._stream_mjpeg("realsense_color")

        elif path == "/realsense/depth":
            self._stream_mjpeg("realsense_depth")

        elif path == "/blackfly":
            self._stream_mjpeg("blackfly")

        elif path == "/snapshot/realsense/color":
            self._send_snapshot("realsense_color")

        elif path == "/snapshot/realsense/depth":
            self._send_snapshot("realsense_depth")

        elif path == "/snapshot/blackfly":
            self._send_snapshot("blackfly")

        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not found. Endpoints: /realsense/color, /realsense/depth, /blackfly, /status")

    def _send_json(self, data):
        import json
        body = json.dumps(data).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_snapshot(self, key):
        with frame_locks[key]:
            frame = latest_frames[key]
        if frame is None:
            self.send_response(503)
            self.end_headers()
            self.wfile.write(b"No frame available")
            return
        self.send_response(200)
        self.send_header("Content-Type", "image/jpeg")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(frame)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(frame)

    def _stream_mjpeg(self, key):
        self.send_response(200)
        self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.end_headers()

        interval = 1.0 / 15  # target ~15 fps delivery
        try:
            while not shutdown_event.is_set():
                with frame_locks[key]:
                    frame = latest_frames[key]

                if frame is not None:
                    self.wfile.write(b"--frame\r\n")
                    self.wfile.write(b"Content-Type: image/jpeg\r\n")
                    self.wfile.write(f"Content-Length: {len(frame)}\r\n".encode())
                    self.wfile.write(b"\r\n")
                    self.wfile.write(frame)
                    self.wfile.write(b"\r\n")

                time.sleep(interval)

        except (BrokenPipeError, ConnectionResetError):
            pass


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    def handler(sig, frame):
        shutdown_event.set()
        sys.exit(0)

    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)

    # Start capture threads
    t_rs = threading.Thread(target=realsense_capture, daemon=True, name="realsense")
    t_bf = threading.Thread(target=blackfly_capture, daemon=True, name="blackfly")
    t_rs.start()
    t_bf.start()

    # Start HTTP server
    server = ThreadedHTTPServer(("0.0.0.0", PORT), CameraHandler)
    print(f"Camera server listening on :{PORT}")
    print(f"  RealSense color: http://0.0.0.0:{PORT}/realsense/color")
    print(f"  RealSense depth: http://0.0.0.0:{PORT}/realsense/depth")
    print(f"  Blackfly:        http://0.0.0.0:{PORT}/blackfly")
    print(f"  Status:          http://0.0.0.0:{PORT}/status")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        shutdown_event.set()
        server.shutdown()


if __name__ == "__main__":
    main()
