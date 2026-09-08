import logging
import json
import sys
import time
from datetime import datetime
from contextvars import ContextVar
from typing import Any, Dict

# Context variable to store request ID
request_id_var: ContextVar[str] = ContextVar("request_id", default="system")

from backend.app.config import settings

class StructuredFormatter(logging.Formatter):
    def __init__(self, service_name: str):
        super().__init__()
        self.service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")
        request_id = request_id_var.get()
        level = record.levelname.ljust(7)
        msg = record.getMessage()
        module_func = f"{record.module}:{record.funcName}"

        # Human-readable format
        log_line = f"[{timestamp}] {level} | {request_id} | {module_func} - {msg}"

        if record.exc_info:
            log_line += "\n" + self.formatException(record.exc_info)

        # Handle extra info if needed (for debug only)
        if hasattr(record, "extra_info") and isinstance(record.extra_info, dict):
            extra = str(record.extra_info)
            log_line += f" | EXTRA: {extra}"

        return log_line

def setup_logging(service_name: str = "loom-api"):
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)

    # Use JSON if explicitly enabled, else human-readable
    if getattr(settings, "LOG_JSON", False):
        class JSONFormatter(logging.Formatter):
            def format(self, record: logging.LogRecord) -> str:
                log_data = {
                    "timestamp": datetime.fromtimestamp(record.created).isoformat(),
                    "level": record.levelname,
                    "service": service_name,
                    "request_id": request_id_var.get(),
                    "message": record.getMessage(),
                    "module": record.module,
                    "function": record.funcName,
                }
                return json.dumps(log_data)
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(StructuredFormatter(service_name))

    root_logger.addHandler(handler)

    # Set levels for some verbose libraries
    logging.getLogger("uvicorn.access").handlers = []
    logging.getLogger("uvicorn.error").handlers = []

    # Mute standard library logs that are too noisy
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    return logging.getLogger(service_name)

logger = logging.getLogger("loom-api")
