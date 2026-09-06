import logging
import json
import sys
import time
from datetime import datetime
from contextvars import ContextVar
from typing import Any, Dict

# Context variable to store request ID
request_id_var: ContextVar[str] = ContextVar("request_id", default="system")

class StructuredFormatter(logging.Formatter):
    def __init__(self, service_name: str):
        super().__init__()
        self.service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "service": self.service_name,
            "request_id": request_id_var.get(),
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields if present
        if hasattr(record, "extra_info") and isinstance(record.extra_info, dict):
            # Filtering out potential secrets (more comprehensive check)
            sensitive_keys = {"password", "token", "key", "secret", "authorization", "github_token", "api_key"}
            filtered_extra = {
                k: v for k, v in record.extra_info.items()
                if not any(sk in k.lower() for sk in sensitive_keys)
            }
            log_data.update(filtered_extra)

        return json.dumps(log_data)

def setup_logging(service_name: str = "loom-api"):
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredFormatter(service_name))
    root_logger.addHandler(handler)

    # Set levels for some verbose libraries
    logging.getLogger("uvicorn.access").handlers = []
    logging.getLogger("uvicorn.error").handlers = []

    return logging.getLogger(service_name)

logger = logging.getLogger("loom-api")
