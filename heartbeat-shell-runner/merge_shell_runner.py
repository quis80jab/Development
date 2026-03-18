#!/usr/bin/env python3
"""
Merge shell-runner add-on into existing Heartbeat app.py and index.html.
Run from heartbeat dir: python3 merge_shell_runner.py
  Reads app.py and index.html, merges shell_routes + shell_runner_section, writes back.
"""
import re
from pathlib import Path

HEARTBEAT_DIR = Path(__file__).resolve().parent


def merge_app_py(app_path: Path, out_path: Path) -> None:
    text = app_path.read_text()
    if "shell_router" in text and "include_router(shell_router" in text:
        print("app.py already includes shell router, skipping.")
        return
    # Add import after the last top-level import
    if "from shell_routes import shell_router" not in text:
        lines = text.split("\n")
        insert_i = 0
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("import ") or stripped.startswith("from "):
                insert_i = i + 1
        lines.insert(insert_i, "from shell_routes import shell_router")
        text = "\n".join(lines)
    if "include_router(shell_router" not in text:
        # Add after "app = FastAPI("
        pattern = r"(app\s*=\s*FastAPI\s*\([^)]*\)\s*\n)"
        m = re.search(pattern, text)
        if m:
            pos = m.end()
            text = (
                text[:pos]
                + 'app.include_router(shell_router, prefix="/api/shell", tags=["shell"])\n'
                + text[pos:]
            )
        else:
            # Before uvicorn.run
            pattern = r"(\n(?:if __name__|uvicorn\.run))"
            m = re.search(pattern, text)
            if m:
                text = (
                    text[: m.start()]
                    + '\napp.include_router(shell_router, prefix="/api/shell", tags=["shell"])\n'
                    + text[m.start() :]
                )
    out_path.write_text(text)
    print("Merged app.py")


def merge_index_html(index_path: Path, section_path: Path, out_path: Path) -> None:
    html = index_path.read_text()
    section = section_path.read_text()
    if "shell-runner-card" in html:
        print("index.html already includes shell runner section, skipping.")
        return
    html = html.replace("</body>", section.strip() + "\n</body>")
    out_path.write_text(html)
    print("Merged index.html")


def main() -> None:
    app_py = HEARTBEAT_DIR / "app.py"
    index_html = HEARTBEAT_DIR / "index.html"
    routes_py = HEARTBEAT_DIR / "shell_routes.py"
    section_html = HEARTBEAT_DIR / "shell_runner_section.html"
    for p in (app_py, index_html, routes_py, section_html):
        if not p.exists():
            raise SystemExit(f"Missing: {p}")
    merge_app_py(app_py, app_py)
    merge_index_html(index_html, section_html, index_html)
    print("Done. Rebuild the heartbeat container.")


if __name__ == "__main__":
    main()
