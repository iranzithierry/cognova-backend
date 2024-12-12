import sys
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler


def setup_logging():
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Configure logging
    logging_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging_format)
    root_logger.addHandler(console_handler)

    file_handler = RotatingFileHandler(
        "logs/app.log", maxBytes=10485760, backupCount=5, encoding="utf-8"  # 10MB
    )
    file_handler.setFormatter(logging_format)
    root_logger.addHandler(file_handler)

    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("httpx").disabled = True
