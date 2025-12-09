"""
Simple structured logging helpers for Lattice backend.
"""

from __future__ import annotations

import logging
import os
from typing import Any


def configure_logger(name: str = "lattice") -> logging.Logger:
    level = os.getenv("LATTICE_LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    return logging.getLogger(name)


def log_event(logger: logging.Logger, level: int, event: str, **fields: Any) -> None:
    parts = [event]
    for key, value in fields.items():
        if value is None:
            continue
        parts.append(f"{key}={value}")
    logger.log(level, " ".join(parts))


__all__ = ["configure_logger", "log_event"]
