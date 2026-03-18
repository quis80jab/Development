import argparse
import io
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

import cv2
import numpy as np


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def do_GET(self):
        # Accept any path so this can stand in for both the middleware
        # (/api/frame) and the camera server (/snapshot/*).

        w, h = self.server.size
        t = time.time()
        img = np.zeros((h, w, 3), dtype=np.uint8)
        cv2.putText(
            img,
            f"Dummy frame {t:.2f}",
            (16, 48),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (0, 255, 0),
            2,
            cv2.LINE_AA,
        )
        ok, jpg = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 80])
        if not ok:
            self.send_response(500)
            self.end_headers()
            return

        body = jpg.tobytes()
        self.send_response(200)
        self.send_header("Content-Type", "image/jpeg")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> int:
    p = argparse.ArgumentParser(description="Serve dummy /api/frame JPEGs for testing.")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8899)
    p.add_argument("--size", default="640x480")
    args = p.parse_args()

    w, h = [int(x) for x in args.size.lower().split("x")]
    httpd = HTTPServer((args.host, args.port), Handler)
    httpd.size = (w, h)
    print(f"Dummy frame server at http://{args.host}:{args.port}/api/frame")
    httpd.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

