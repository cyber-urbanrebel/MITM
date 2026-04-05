"""
addons/modifier.py — Intercepts requests and responses and applies
configurable modifications.

Examples of what this addon can do:
  • Inject or override request/response headers
  • Replace text in response bodies (string substitution)
  • Add CORS headers to every response (useful for local API testing)

Edit the HEADER_INJECTIONS, RESPONSE_HEADER_INJECTIONS, and BODY_REPLACEMENTS
dictionaries below, or subclass / extend Modifier for more complex scenarios.
"""

import logging

from mitmproxy import ctx, http

_log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration — edit these to suit your needs
# ---------------------------------------------------------------------------

# Headers added to every *request* before it is forwarded upstream.
# Format: {header_name: header_value}
REQUEST_HEADER_INJECTIONS: dict[str, str] = {
    # "X-Forwarded-For": "127.0.0.1",
}

# Headers added to every *response* before it is returned to the client.
RESPONSE_HEADER_INJECTIONS: dict[str, str] = {
    # Uncomment to add permissive CORS headers to every response:
    # "Access-Control-Allow-Origin": "*",
    # "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    # "Access-Control-Allow-Headers": "*",
}

# Simple find-and-replace pairs applied to *text* response bodies.
# Format: {find_bytes: replace_bytes}
# Only applied when the response Content-Type contains "text".
BODY_REPLACEMENTS: dict[bytes, bytes] = {
    # b"example.com": b"replaced.example.com",
}


class Modifier:
    """mitmproxy addon that injects headers and rewrites response bodies."""

    # ------------------------------------------------------------------
    # mitmproxy hooks
    # ------------------------------------------------------------------

    def request(self, flow: http.HTTPFlow) -> None:
        for name, value in REQUEST_HEADER_INJECTIONS.items():
            flow.request.headers[name] = value
            try:
                ctx.log.debug(f"[Modifier] Injected request header: {name}: {value}")
            except AttributeError:
                _log.debug("[Modifier] Injected request header: %s: %s", name, value)

    def response(self, flow: http.HTTPFlow) -> None:
        resp = flow.response

        # Inject response headers
        for name, value in RESPONSE_HEADER_INJECTIONS.items():
            resp.headers[name] = value
            try:
                ctx.log.debug(f"[Modifier] Injected response header: {name}: {value}")
            except AttributeError:
                _log.debug("[Modifier] Injected response header: %s: %s", name, value)

        # Apply body replacements for text responses
        if not BODY_REPLACEMENTS:
            return

        content_type = resp.headers.get("content-type", "")
        if "text" not in content_type:
            return

        content = resp.content
        modified = False
        for find, replace in BODY_REPLACEMENTS.items():
            if find in content:
                content = content.replace(find, replace)
                modified = True
                try:
                    ctx.log.info(
                        f"[Modifier] Replaced {find!r} → {replace!r} "
                        f"in response from {flow.request.pretty_url}"
                    )
                except AttributeError:
                    _log.info(
                        "[Modifier] Replaced %r -> %r in response from %s",
                        find, replace, flow.request.pretty_url,
                    )

        if modified:
            resp.content = content


addons = [Modifier()]
