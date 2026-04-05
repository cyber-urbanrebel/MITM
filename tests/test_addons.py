"""
tests/test_addons.py — Unit tests for the MITM proxy addons.

Tests run with pytest and use mitmproxy's built-in testing helpers
(mitmproxy.test.tflow, mitmproxy.test.taddons) so no live network
connection is required.
"""

import json
import os
import re
import sys

import pytest

# Ensure the repo root is on sys.path so that `addons` can be imported.
REPO_ROOT = os.path.dirname(os.path.dirname(__file__))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from mitmproxy import http
from mitmproxy.test import tflow


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_request_flow(
    url: str = "http://example.com/",
    method: str = "GET",
    headers: dict | None = None,
    body: bytes = b"",
) -> http.HTTPFlow:
    """Return a simple HTTPFlow with the given request parameters."""
    req = http.Request.make(method, url, body, headers or {})
    f = tflow.tflow(req=req)
    return f


def _make_response_flow(
    url: str = "http://example.com/",
    status_code: int = 200,
    content: bytes = b"Hello world",
    content_type: str = "text/html",
) -> http.HTTPFlow:
    """Return an HTTPFlow that already has a response attached."""
    f = _make_request_flow(url)
    f.response = http.Response.make(
        status_code,
        content,
        {"Content-Type": content_type},
    )
    return f


# ---------------------------------------------------------------------------
# Logger tests
# ---------------------------------------------------------------------------

class TestLogger:
    def test_request_logged(self, tmp_path, monkeypatch):
        """Logger should write a JSON-Lines entry for each request."""
        log_file = tmp_path / "traffic.log"

        import addons.logger as logger_mod
        monkeypatch.setattr(logger_mod, "LOG_FILE", str(log_file))
        monkeypatch.setattr(logger_mod, "LOG_DIR", str(tmp_path))

        logger = logger_mod.TrafficLogger()
        flow = _make_request_flow("http://example.com/path?q=1")
        logger.request(flow)

        lines = log_file.read_text().strip().splitlines()
        assert len(lines) == 1
        entry = json.loads(lines[0])
        assert entry["type"] == "request"
        assert "example.com" in entry["url"]
        assert entry["method"] == "GET"

    def test_response_logged(self, tmp_path, monkeypatch):
        """Logger should write a JSON-Lines entry for each response."""
        log_file = tmp_path / "traffic.log"

        import addons.logger as logger_mod
        monkeypatch.setattr(logger_mod, "LOG_FILE", str(log_file))
        monkeypatch.setattr(logger_mod, "LOG_DIR", str(tmp_path))

        logger = logger_mod.TrafficLogger()
        flow = _make_response_flow("http://example.com/", status_code=200)
        logger.response(flow)

        lines = log_file.read_text().strip().splitlines()
        assert len(lines) == 1
        entry = json.loads(lines[0])
        assert entry["type"] == "response"
        assert entry["status_code"] == 200

    def test_body_truncation(self, tmp_path, monkeypatch):
        """Bodies longer than 2048 chars should be truncated in the log."""
        log_file = tmp_path / "traffic.log"

        import addons.logger as logger_mod
        monkeypatch.setattr(logger_mod, "LOG_FILE", str(log_file))
        monkeypatch.setattr(logger_mod, "LOG_DIR", str(tmp_path))

        long_body = b"A" * 4000
        flow = _make_response_flow(content=long_body)
        logger = logger_mod.TrafficLogger()
        logger.response(flow)

        entry = json.loads(log_file.read_text().strip())
        assert "truncated" in entry["body"]
        assert len(entry["body"]) < 4000

    def test_truncate_helper_bytes(self):
        import addons.logger as logger_mod
        result = logger_mod._truncate(b"x" * 3000)
        assert "truncated" in result

    def test_truncate_helper_str_short(self):
        import addons.logger as logger_mod
        result = logger_mod._truncate("hello")
        assert result == "hello"


# ---------------------------------------------------------------------------
# Blocker tests
# ---------------------------------------------------------------------------

class TestBlocker:
    def _make_blocker(self):
        import addons.blocker as blocker_mod
        return blocker_mod.Blocker()

    def test_blocks_doubleclick(self):
        """Requests to doubleclick.net should be blocked with HTTP 403."""
        blocker = self._make_blocker()
        flow = _make_request_flow("https://ad.doubleclick.net/banner?id=123")
        blocker.request(flow)
        assert flow.response is not None
        assert flow.response.status_code == 403

    def test_blocks_google_analytics(self):
        blocker = self._make_blocker()
        flow = _make_request_flow("https://www.google-analytics.com/collect")
        blocker.request(flow)
        assert flow.response is not None
        assert flow.response.status_code == 403

    def test_allows_normal_traffic(self):
        """Requests to unblocked URLs should pass through unchanged."""
        blocker = self._make_blocker()
        flow = _make_request_flow("https://www.example.com/page")
        blocker.request(flow)
        assert flow.response is None

    def test_compile_invalid_pattern(self):
        """Invalid regex patterns should be skipped without crashing."""
        import addons.blocker as blocker_mod
        patterns = blocker_mod._compile(["[invalid_regex"])
        assert patterns == []

    def test_compile_valid_patterns(self):
        import addons.blocker as blocker_mod
        patterns = blocker_mod._compile([r"example\.com", r"test\.org"])
        assert len(patterns) == 2
        assert all(isinstance(p, re.Pattern) for p in patterns)


# ---------------------------------------------------------------------------
# Modifier tests
# ---------------------------------------------------------------------------

class TestModifier:
    def _make_modifier(self):
        import addons.modifier as modifier_mod
        return modifier_mod.Modifier()

    def test_no_injections_by_default(self):
        """With empty injection dicts, flows should be passed through unchanged."""
        import addons.modifier as modifier_mod

        original_req_headers = dict(modifier_mod.REQUEST_HEADER_INJECTIONS)
        original_resp_headers = dict(modifier_mod.RESPONSE_HEADER_INJECTIONS)
        modifier_mod.REQUEST_HEADER_INJECTIONS.clear()
        modifier_mod.RESPONSE_HEADER_INJECTIONS.clear()

        try:
            modifier = self._make_modifier()
            flow = _make_response_flow()
            modifier.request(flow)
            modifier.response(flow)
        finally:
            modifier_mod.REQUEST_HEADER_INJECTIONS.update(original_req_headers)
            modifier_mod.RESPONSE_HEADER_INJECTIONS.update(original_resp_headers)

    def test_request_header_injection(self):
        """Configured request headers should be injected into the flow."""
        import addons.modifier as modifier_mod

        modifier_mod.REQUEST_HEADER_INJECTIONS["X-Test-Header"] = "test-value"
        try:
            modifier = self._make_modifier()
            flow = _make_request_flow()
            modifier.request(flow)
            assert flow.request.headers.get("X-Test-Header") == "test-value"
        finally:
            del modifier_mod.REQUEST_HEADER_INJECTIONS["X-Test-Header"]

    def test_response_header_injection(self):
        """Configured response headers should be injected into the flow."""
        import addons.modifier as modifier_mod

        modifier_mod.RESPONSE_HEADER_INJECTIONS["X-Custom-Response"] = "custom-value"
        try:
            modifier = self._make_modifier()
            flow = _make_response_flow()
            modifier.response(flow)
            assert flow.response.headers.get("X-Custom-Response") == "custom-value"
        finally:
            del modifier_mod.RESPONSE_HEADER_INJECTIONS["X-Custom-Response"]

    def test_body_replacement_text(self):
        """Body replacements should be applied to text response bodies."""
        import addons.modifier as modifier_mod

        modifier_mod.BODY_REPLACEMENTS[b"Hello world"] = b"Goodbye world"
        try:
            modifier = self._make_modifier()
            flow = _make_response_flow(content=b"Hello world", content_type="text/html")
            modifier.response(flow)
            assert flow.response.content == b"Goodbye world"
        finally:
            del modifier_mod.BODY_REPLACEMENTS[b"Hello world"]

    def test_body_replacement_skipped_for_non_text(self):
        """Body replacements should NOT be applied to binary (non-text) responses."""
        import addons.modifier as modifier_mod

        modifier_mod.BODY_REPLACEMENTS[b"Hello"] = b"Goodbye"
        try:
            modifier = self._make_modifier()
            flow = _make_response_flow(
                content=b"Hello",
                content_type="application/octet-stream",
            )
            modifier.response(flow)
            assert flow.response.content == b"Hello"
        finally:
            del modifier_mod.BODY_REPLACEMENTS[b"Hello"]


# ---------------------------------------------------------------------------
# proxy.py / webui.py argument parsing tests
# ---------------------------------------------------------------------------

class TestProxyArgs:
    def test_default_port(self, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["proxy.py"])
        import proxy as proxy_mod
        args = proxy_mod.parse_args()
        assert args.port == 8080

    def test_custom_port(self, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["proxy.py", "--port", "9090"])
        import proxy as proxy_mod
        args = proxy_mod.parse_args()
        assert args.port == 9090

    def test_no_blocker_flag(self, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["proxy.py", "--no-blocker"])
        import proxy as proxy_mod
        args = proxy_mod.parse_args()
        assert args.no_blocker is True

    def test_command_includes_addons(self, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["proxy.py"])
        import proxy as proxy_mod
        args = proxy_mod.parse_args()
        cmd = proxy_mod.build_command(args)
        assert "addons/logger.py" in cmd
        assert "addons/blocker.py" in cmd
        assert "addons/modifier.py" in cmd

    def test_command_excludes_disabled_addons(self, monkeypatch):
        monkeypatch.setattr(
            sys, "argv",
            ["proxy.py", "--no-logger", "--no-blocker", "--no-modifier"],
        )
        import proxy as proxy_mod
        args = proxy_mod.parse_args()
        cmd = proxy_mod.build_command(args)
        assert "addons/logger.py" not in cmd
        assert "addons/blocker.py" not in cmd
        assert "addons/modifier.py" not in cmd


class TestWebuiArgs:
    def test_default_ports(self, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["webui.py"])
        import webui as webui_mod
        args = webui_mod.parse_args()
        assert args.port == 8080
        assert args.web_port == 8081

    def test_custom_web_port(self, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["webui.py", "--web-port", "9000"])
        import webui as webui_mod
        args = webui_mod.parse_args()
        assert args.web_port == 9000

    def test_command_includes_web_port(self, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["webui.py"])
        import webui as webui_mod
        args = webui_mod.parse_args()
        cmd = webui_mod.build_command(args)
        assert "--web-port" in cmd
        assert "8081" in cmd
