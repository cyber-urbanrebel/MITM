# mitm-proxy

A local HTTPS Man-in-the-Middle (MITM) proxy project using mitmproxy and cryptography.

## Features
- Intercept and inspect HTTPS traffic
- Customizable proxy logic
- Built with [mitmproxy](https://mitmproxy.org/) and [cryptography](https://cryptography.io/)

## Setup

1. **Python Environment**
   - Python 3.13+ (virtual environment is set up automatically)

2. **Install dependencies**
   - Already installed: `mitmproxy`, `cryptography`

3. **Development**
   - Start building your custom proxy logic in `proxy_main.py`.

## Usage

- To run mitmproxy interactively:
  ```bash
  mitmproxy
  ```
- To run your custom proxy script:
  ```bash
  c:/Users/USER/OneDrive/MITM/.venv/Scripts/python.exe proxy_main.py
  ```

## Next Steps
- Implement your proxy logic in `proxy_main.py`
- See mitmproxy docs for scripting examples

---

MIT License
