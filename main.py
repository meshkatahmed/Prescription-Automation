import os
import uvicorn

def main() -> None:
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", 8000))
    reload_flag = os.environ.get("RELOAD", "true").lower() in {"1", "true", "yes"}

    uvicorn.run(
        "prescription_automation.api.v1:app",
        host=host,
        port=port,
        reload=reload_flag,
    )


if __name__ == "__main__":
    main()
