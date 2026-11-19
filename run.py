import threading
import time
import webbrowser
import uvicorn
from app.config import get_settings


def auto_open_browser(port: int):
    """Opens browser at the configured port after a brief delay."""
    time.sleep(1.2)
    try:
        webbrowser.open(f"http://127.0.0.1:{port}")
    except Exception:
        pass


if __name__ == "__main__":
    settings = get_settings()
    print(f"\n🚀 Starting Daily Report AI on http://127.0.0.1:{settings.PORT}")
    print(f"🌐 Opening in your browser: http://127.0.0.1:{settings.PORT}")
    print("Press CTRL+C to stop the server\n")

    # Launch browser automatically
    threading.Thread(target=auto_open_browser, args=(settings.PORT,), daemon=True).start()

    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=settings.PORT,
        reload=True,
    )

