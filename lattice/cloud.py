"""
Background uploader for optional AgentRouter cloud ingestion.
"""

from __future__ import annotations

import queue
import threading
from typing import Any, Dict, Optional

import requests

from .config import settings
from .logging import configure_logger

logger = configure_logger("lattice.cloud")


class CloudIngestor:
    """
    Very small async queue that forwards metadata to the AgentRouter cloud endpoint.
    """

    def __init__(self) -> None:
        self._enabled = bool(settings.cloud_ingest_key)
        self._queue: "queue.SimpleQueue[Optional[Dict[str, Any]]]" = queue.SimpleQueue()
        self._thread: Optional[threading.Thread] = None

        if self._enabled:
            self._thread = threading.Thread(target=self._worker, name="lattice-cloud-ingest", daemon=True)
            self._thread.start()

    def enqueue(self, payload: Dict[str, Any]) -> None:
        if not self._enabled or not payload:
            return
        self._queue.put(payload)

    def _worker(self) -> None:
        headers = {
            "Authorization": f"Bearer {settings.cloud_ingest_key}",
            "Content-Type": "application/json",
        }
        endpoint = settings.cloud_ingest_url.rstrip("/")

        while True:
            payload = self._queue.get()
            if payload is None:
                break
            try:
                requests.post(endpoint, json=payload, headers=headers, timeout=2.0)
            except Exception:
                # Ingest failures should never block the completion flow.
                logger.debug("cloud_ingest_failed", exc_info=True)

    def shutdown(self) -> None:
        if not self._enabled:
            return
        self._queue.put(None)


_INGESTOR = CloudIngestor()


def enqueue_cloud_ingest(payload: Dict[str, Any]) -> None:
    """
    Submit a metadata payload for background ingestion if enabled.
    """

    _INGESTOR.enqueue(payload)


__all__ = ["enqueue_cloud_ingest"]
