import logging
import os
from pathlib import Path

import uvicorn


def configure_logging() -> None:
    log_dir = Path(os.getenv("TIMETABLING_LOG_DIR", Path.cwd() / "logs"))
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "backend-startup.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def main() -> None:
    configure_logging()
    os.environ.setdefault("TIMETABLING_APP_ENV", "desktop")
    host = os.getenv("TIMETABLING_HOST", "127.0.0.1")
    port = int(os.getenv("TIMETABLING_PORT", "8000"))
    uvicorn.run("app.main:app", host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
