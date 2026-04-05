"""
addons/blocker.py — Blocks requests whose URLs match a configurable blocklist.

Default patterns cover common ad/tracker domains.  Add your own patterns to
BLOCK_PATTERNS below or pass them at runtime via the mitmproxy option:

    mitmdump --set block_patterns=ads.example.com,tracker.io -s addons/blocker.py

Blocked requests receive an immediate 403 response; the upstream server is
never contacted.
"""

import logging
import re

from mitmproxy import ctx, http

_log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Default blocklist — extend as needed
# ---------------------------------------------------------------------------
DEFAULT_BLOCK_PATTERNS: list[str] = [
    # Ad networks
    r"doubleclick\.net",
    r"googlesyndication\.com",
    r"adservice\.google\.",
    r"ads\.twitter\.com",
    r"advertising\.com",
    r"adnxs\.com",
    r"taboola\.com",
    r"outbrain\.com",
    r"moatads\.com",
    # Tracking / analytics
    r"google-analytics\.com",
    r"googletagmanager\.com",
    r"facebook\.com/tr",
    r"analytics\.tiktok\.com",
    r"scorecardresearch\.com",
    r"quantserve\.com",
    r"hotjar\.com",
]


def _compile(patterns: list[str]) -> list[re.Pattern]:
    compiled = []
    for p in patterns:
        try:
            compiled.append(re.compile(p, re.IGNORECASE))
        except re.error as exc:
            _log.warning("[Blocker] Invalid pattern '%s': %s", p, exc)
    return compiled


class Blocker:
    """mitmproxy addon that blocks matching URLs."""

    def __init__(self) -> None:
        self._patterns: list[re.Pattern] = _compile(DEFAULT_BLOCK_PATTERNS)

    # ------------------------------------------------------------------
    # mitmproxy option hooks
    # ------------------------------------------------------------------

    def load(self, loader) -> None:  # noqa: ARG002
        loader.add_option(
            name="block_patterns",
            typespec=str,
            default="",
            help=(
                "Comma-separated list of regex patterns. "
                "Requests whose URL matches any pattern are blocked."
            ),
        )

    def configure(self, updates) -> None:
        if "block_patterns" in updates:
            raw = ctx.options.block_patterns.strip()
            extra = [p.strip() for p in raw.split(",") if p.strip()]
            self._patterns = _compile(DEFAULT_BLOCK_PATTERNS + extra)
            try:
                ctx.log.info(f"[Blocker] Active patterns: {len(self._patterns)}")
            except AttributeError:
                _log.info("[Blocker] Active patterns: %d", len(self._patterns))

    # ------------------------------------------------------------------
    # mitmproxy request hook
    # ------------------------------------------------------------------

    def request(self, flow: http.HTTPFlow) -> None:
        url = flow.request.pretty_url
        for pattern in self._patterns:
            if pattern.search(url):
                try:
                    ctx.log.info(f"[Blocker] Blocked: {url}  (matched: {pattern.pattern})")
                except AttributeError:
                    _log.info("[Blocker] Blocked: %s  (matched: %s)", url, pattern.pattern)
                flow.response = http.Response.make(
                    403,
                    b"Blocked by MITM proxy",
                    {"Content-Type": "text/plain"},
                )
                return


addons = [Blocker()]
