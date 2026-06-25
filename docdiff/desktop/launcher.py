from __future__ import annotations

import os
import sys
import threading
import time
import webbrowser

from pathlib import Path

# Add project root to sys.path for direct execution without pip install
_project_root = Path(__file__).parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import uvicorn

from docdiff.webapp.app import app


def _run_server(host: str = "127.0.0.1", port: int = 8765) -> None:
    """Run the FastAPI server in the current thread."""
    uvicorn.run(app, host=host, port=port, log_level="warning")


def _wait_for_server(host: str, port: int, timeout: float = 15.0) -> bool:
    import socket
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except OSError:
            time.sleep(0.2)
    return False


def launch(host: str = "127.0.0.1", port: int = 8765, open_browser: bool = True) -> None:
    """Launch DocDiff desktop app: start server and open browser."""
    # Start server in a background thread
    server_thread = threading.Thread(
        target=_run_server,
        kwargs={"host": host, "port": port},
        daemon=True,
    )
    server_thread.start()

    print(f"🚀 DocDiff запускается...")
    print(f"   Сервер: http://{host}:{port}")

    if open_browser:
        if _wait_for_server(host, port):
            url = f"http://{host}:{port}"
            print(f"   Открываю браузер...")
            webbrowser.open(url)
        else:
            print(f"   ⚠️ Сервер не запустился за {15} секунд. Откройте http://{host}:{port} вручную.")

    try:
        # Keep main thread alive
        while server_thread.is_alive():
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 Завершение работы...")
        sys.exit(0)


def main() -> None:
    """Entry point for `docdiff-gui` or `python -m docdiff.desktop`."""
    launch()


if __name__ == "__main__":
    main()
