import uvicorn
from app.config import get_settings

if __name__ == "__main__":
    settings = get_settings()
    print(f"\n🚀 Starting Daily Report AI on http://127.0.0.1:{settings.PORT}")
    print("Press CTRL+C to stop the server\n")
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=settings.PORT,
        reload=True,
    )

