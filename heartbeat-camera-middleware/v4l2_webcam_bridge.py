import argparse
import os
import signal
import subprocess
import sys
import time
from typing import Optional, Tuple

import cv2
import httpx
import numpy as np


def _parse_size(value: str) -> Tuple[int, int]:
    parts = value.lower().split("x")
    if len(parts) != 2:
        raise argparse.ArgumentTypeError("Size must be like 640x480")
    return int(parts[0]), int(parts[1])


def _decode_jpeg(jpeg_bytes: bytes) -> Optional[np.ndarray]:
    arr = np.frombuffer(jpeg_bytes, dtype=np.uint8)
    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    return frame


def _start_ffmpeg_v4l2_writer(
    device: str, width: int, height: int, fps: int, ffmpeg_bin: str = "ffmpeg"
) -> subprocess.Popen:
    # Feed raw BGR frames into ffmpeg stdin; ffmpeg writes to v4l2loopback device.
    #
    # Using rawvideo avoids any additional JPEG encode work in this bridge.
    cmd = [
        ffmpeg_bin,
        "-hide_banner",
        "-loglevel",
        "error",
        "-re",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "bgr24",
        "-s",
        f"{width}x{height}",
        "-r",
        str(fps),
        "-i",
        "pipe:0",
        "-f",
        "v4l2",
        device,
    ]
    return subprocess.Popen(cmd, stdin=subprocess.PIPE)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Bridge Heartbeat camera middleware frames into a v4l2loopback webcam device."
    )
    parser.add_argument(
        "--source",
        default=os.environ.get("CAM_MW_SOURCE", "http://127.0.0.1:8891/api/frame"),
        help="JPEG frame URL (default: http://127.0.0.1:8891/api/frame)",
    )
    parser.add_argument(
        "--device",
        default=os.environ.get("V4L2_DEVICE", "/dev/video10"),
        help="v4l2loopback device path (default: /dev/video10)",
    )
    parser.add_argument(
        "--size",
        type=_parse_size,
        default=_parse_size(os.environ.get("V4L2_SIZE", "640x480")),
        help="Output size WxH (default: 640x480)",
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=int(os.environ.get("V4L2_FPS", "15")),
        help="Output fps to virtual webcam (default: 15)",
    )
    parser.add_argument(
        "--poll-fps",
        type=float,
        default=float(os.environ.get("V4L2_POLL_FPS", "10")),
        help="How often to pull JPEG frames (default: 10)",
    )
    parser.add_argument(
        "--ffmpeg",
        default=os.environ.get("FFMPEG_BIN", "ffmpeg"),
        help="ffmpeg binary (default: ffmpeg)",
    )
    args = parser.parse_args()

    width, height = args.size
    poll_interval = 1.0 / max(args.poll_fps, 0.1)
    stop = False

    def handle_sig(*_):
        nonlocal stop
        stop = True

    signal.signal(signal.SIGINT, handle_sig)
    signal.signal(signal.SIGTERM, handle_sig)

    proc = _start_ffmpeg_v4l2_writer(args.device, width, height, args.fps, args.ffmpeg)
    if proc.stdin is None:
        print("ffmpeg stdin unavailable", file=sys.stderr)
        return 2

    last_ok = 0.0
    try:
        with httpx.Client(timeout=httpx.Timeout(3.0, read=3.0)) as client:
            while not stop:
                try:
                    resp = client.get(args.source, headers={"Cache-Control": "no-cache"})
                    if resp.status_code != 200:
                        time.sleep(poll_interval)
                        continue

                    frame = _decode_jpeg(resp.content)
                    if frame is None:
                        time.sleep(poll_interval)
                        continue

                    if (frame.shape[1], frame.shape[0]) != (width, height):
                        frame = cv2.resize(frame, (width, height), interpolation=cv2.INTER_AREA)

                    proc.stdin.write(frame.tobytes())
                    proc.stdin.flush()
                    last_ok = time.time()

                except BrokenPipeError:
                    print("ffmpeg pipe closed", file=sys.stderr)
                    return 3
                except Exception:
                    # If cameras are offline, /api/frame may 503; keep looping.
                    time.sleep(poll_interval)

                # If we've had no successful frames for a while, still keep the writer alive.
                if last_ok and (time.time() - last_ok) > 10:
                    last_ok = time.time()

                time.sleep(poll_interval)
    finally:
        try:
            proc.stdin.close()
        except Exception:
            pass
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

