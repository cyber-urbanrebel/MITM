"""
addons/logger.py — Logs every intercepted HTTP/HTTPS request and response.

Each flow is written to:
  • stdout   (human-readable summary)
  • logs/traffic.log  (JSON-Lines format for machine consumption)
"""

import json
import logging
import os
import time

from mitmproxy import ctx, http

_log = logging.getLogger(__name__)


LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
LOG_FILE = os.path.join(LOG_DIR, "traffic.log")


def _ensure_log_dir() -> None:
    os.makedirs(LOG_DIR, exist_ok=True)


def _truncate(value: str | bytes, limit: int = 2048) -> str:
    """Return a UTF-8 string, truncated to *limit* characters."""
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="replace")
    if len(value) > limit:
        return value[:limit] + f"… [truncated {len(value) - limit} chars]"
    return value


class TrafficLogger:
    """mitmproxy addon that logs requests and responses."""

    def __init__(self) -> None:
        _ensure_log_dir()

    # ------------------------------------------------------------------
    # mitmproxy hooks
    # ------------------------------------------------------------------

    def request(self, flow: http.HTTPFlow) -> None:
        req = flow.request
        entry = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "type": "request",
            "method": req.method,
            "url": req.pretty_url,
            "http_version": req.http_version,
            "headers": dict(req.headers),
            "body": _truncate(req.content or b""),
        }
        self._log(entry)
        try:
            ctx.log.info(
                f"[REQ]  {req.method} {req.pretty_url}"
            )
        except AttributeError:
            _log.info("[REQ]  %s %s", req.method, req.pretty_url)

    def response(self, flow: http.HTTPFlow) -> None:
        resp = flow.response
        entry = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "type": "response",
            "url": flow.request.pretty_url,
            "status_code": resp.status_code,
            "reason": resp.reason,
            "http_version": resp.http_version,
            "headers": dict(resp.headers),
            "body": _truncate(resp.content or b""),
        }
        self._log(entry)
        try:
            ctx.log.info(
                f"[RESP] {resp.status_code} {resp.reason}  ← {flow.request.pretty_url}"
            )
        except AttributeError:
            _log.info("[RESP] %s %s  <- %s", resp.status_code, resp.reason, flow.request.pretty_url)

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    def _log(self, entry: dict) -> None:
        line = json.dumps(entry, ensure_ascii=False)
        with open(LOG_FILE, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")


def load(loader):  # noqa: ARG001 — required mitmproxy hook signature
    """Called by mitmproxy when the addon is loaded."""
    _ensure_log_dir()


addons = [TrafficLogger()]
