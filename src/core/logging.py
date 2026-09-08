"""
Structured Observability Logging with Correlation Context.
"""

import json
import logging
import sys
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any, Dict, Optional

# Context variables for distributed tracing
correlation_id_ctx: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)
task_id_ctx: ContextVar[Optional[str]] = ContextVar("task_id", default=None)
agent_id_ctx: ContextVar[Optional[str]] = ContextVar("agent_id", default=None)


class StructuredJsonFormatter(logging.Formatter):
    """Formats log records as structured JSON."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": correlation_id_ctx.get(),
            "task_id": task_id_ctx.get(),
            "agent_id": agent_id_ctx.get(),
        }

        # Include custom extra attributes
        if hasattr(record, "extra_data") and isinstance(record.extra_data, dict):
            log_entry["data"] = record.extra_data

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


class ConsoleFormatter(logging.Formatter):
    """Human-readable console log formatter."""

    def format(self, record: logging.LogRecord) -> str:
        cid = correlation_id_ctx.get()
        cid_str = f" [{cid[:8]}]" if cid else ""
        return f"[{record.levelname[:4]}] {record.name}{cid_str}: {record.getMessage()}"


def setup_logger(name: str = "ai_operating_model", level: str = "INFO", json_output: bool = False) -> logging.Logger:
    """Configure and return a structured logger."""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Avoid duplicate handlers
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        if json_output:
            handler.setFormatter(StructuredJsonFormatter())
        else:
            handler.setFormatter(ConsoleFormatter())
        logger.addHandler(handler)

    return logger


# Default logger instance
logger = setup_logger()
