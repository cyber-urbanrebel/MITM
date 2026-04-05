# MITM Proxy

A Python-based local HTTPS Man-in-the-Middle (MITM) proxy built on [mitmproxy](https://mitmproxy.org/) and [cryptography](https://cryptography.io/).  
Intercept, inspect, log, block, and modify HTTP/HTTPS traffic — with both a command-line interface and a browser-based web UI.

> **Intended use:** Debugging, testing, and security research on networks and devices you own or have explicit permission to test.

---

## Features

| Feature | Description |
|---|---|
| **Traffic logging** | Every request and response is logged to stdout and `logs/traffic.log` (JSON-Lines) |
| **Ad / tracker blocking** | Built-in blocklist of common ad networks and analytics endpoints; fully configurable |
| **Request / response modification** | Inject headers, rewrite response bodies |
| **CLI mode** | `mitmdump`-based, scriptable and pipeline-friendly |
| **Web UI mode** | `mitmweb` browser interface for real-time, interactive traffic analysis |
| **HTTPS interception** | Full TLS termination via mitmproxy's auto-generated CA certificate |

---

## Project Structure

```
MITM/
├── addons/
│   ├── __init__.py
│   ├── logger.py       # Logs requests & responses (stdout + logs/traffic.log)
│   ├── blocker.py      # Blocks URLs matching the configurable blocklist
│   └── modifier.py     # Injects headers / rewrites response bodies
├── logs/               # Traffic logs written here (gitignored)
├── tests/
│   └── test_addons.py  # pytest test suite
├── proxy.py            # CLI proxy launcher (mitmdump)
├── webui.py            # Web UI proxy launcher (mitmweb)
├── requirements.txt
├── setup.sh            # One-step virtual environment setup
└── README.md
```

---

## Quick Start

### 1. Clone and set up

```bash
git clone https://github.com/cyber-urbanrebel/MITM.git
cd MITM
bash setup.sh
source venv/bin/activate
```

### 2. Run the proxy

**Command-line mode** (terminal output):
```bash
python proxy.py
```

**Web UI mode** (browser interface):
```bash
python webui.py
# Then open http://127.0.0.1:8081 in your browser
```

### 3. Configure your browser / device

Set your browser or device's HTTP/HTTPS proxy to:

| Setting | Value |
|---|---|
| Proxy host | `<this machine's IP>` |
| Proxy port | `8080` (default) |

### 4. Install the CA certificate (HTTPS)

On first run, mitmproxy generates a CA certificate at:

```
~/.mitmproxy/mitmproxy-ca-cert.pem
```

Install this certificate in your browser or OS trust store so that HTTPS traffic can be intercepted and decrypted.

- **Firefox:** Settings → Privacy & Security → View Certificates → Import
- **Chrome / Chromium:** Uses the OS store — import via your system's certificate manager
- **macOS:** `sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain ~/.mitmproxy/mitmproxy-ca-cert.pem`
- **Ubuntu / Debian:** Copy to `/usr/local/share/ca-certificates/mitmproxy.crt` then run `sudo update-ca-certificates`
- **Windows:** Double-click the `.pem` file → Install Certificate → Local Machine → Trusted Root CAs

---

## CLI Options

### `proxy.py` (CLI mode)

```
python proxy.py [--port PORT] [--block PATTERN]
                [--no-logger] [--no-blocker] [--no-modifier]
```

| Flag | Default | Description |
|---|---|---|
| `--port` / `-p` | `8080` | Proxy listen port |
| `--block` | — | Extra comma-separated regex patterns to block |
| `--no-logger` | — | Disable the traffic logger |
| `--no-blocker` | — | Disable the URL blocker |
| `--no-modifier` | — | Disable the request/response modifier |

**Examples:**
```bash
# Default — all addons, port 8080
python proxy.py

# Custom port, extra block pattern
python proxy.py --port 8888 --block "ads\.example\.com"

# Logger only (no blocking, no modification)
python proxy.py --no-blocker --no-modifier
```

### `webui.py` (Web UI mode)

```
python webui.py [--port PORT] [--web-port WEB_PORT]
                [--no-logger] [--no-blocker] [--no-modifier]
```

| Flag | Default | Description |
|---|---|---|
| `--port` / `-p` | `8080` | Proxy listen port |
| `--web-port` / `-w` | `8081` | mitmweb HTTP interface port |
| `--no-logger` | — | Disable the traffic logger |
| `--no-blocker` | — | Disable the URL blocker |
| `--no-modifier` | — | Disable the request/response modifier |

**Examples:**
```bash
# Default
python webui.py

# Custom ports
python webui.py --port 8888 --web-port 9000
```

---

## Customising the Addons

### Blocking additional URLs (`addons/blocker.py`)

Edit `DEFAULT_BLOCK_PATTERNS` to add or remove regex patterns:

```python
DEFAULT_BLOCK_PATTERNS = [
    r"doubleclick\.net",
    r"google-analytics\.com",
    r"my-custom-ad-server\.com",   # <-- add your own
    ...
]
```

Or pass extra patterns at runtime:
```bash
python proxy.py --block "ads\.example\.com,tracker\.io"
```

### Modifying requests and responses (`addons/modifier.py`)

Edit the dictionaries at the top of the file:

```python
# Inject a custom header into every request
REQUEST_HEADER_INJECTIONS = {
    "X-Forwarded-For": "127.0.0.1",
}

# Add CORS headers to every response
RESPONSE_HEADER_INJECTIONS = {
    "Access-Control-Allow-Origin": "*",
}

# Replace text in response bodies
BODY_REPLACEMENTS = {
    b"example.com": b"replaced.example.com",
}
```

### Traffic log format (`logs/traffic.log`)

Each line is a JSON object:

```json
{"timestamp": "2024-01-01T12:00:00Z", "type": "request", "method": "GET", "url": "https://example.com/", "http_version": "HTTP/1.1", "headers": {...}, "body": ""}
{"timestamp": "2024-01-01T12:00:01Z", "type": "response", "url": "https://example.com/", "status_code": 200, "reason": "OK", "http_version": "HTTP/1.1", "headers": {...}, "body": "..."}
```

---

## Running the Tests

```bash
source venv/bin/activate
python -m pytest tests/ -v
```

---

## Security Notes

- This tool performs a **MITM attack on TLS traffic** — only use it on networks and devices you own or have explicit authorisation to test.
- The generated CA certificate is a **root of trust**. Keep it and the corresponding private key (`~/.mitmproxy/mitmproxy-ca.pem`) secure.
- The web UI (`mitmweb`) binds to `127.0.0.1` by default. Do not expose it to the network.
- Never install the mitmproxy CA certificate on production systems or shared machines.

---

## Dependencies

| Package | Purpose |
|---|---|
| `mitmproxy >= 10.0.0` | Core proxy engine, TLS interception, `mitmdump`, `mitmweb` |
| `cryptography >= 41.0.0` | Certificate generation and TLS primitives |

