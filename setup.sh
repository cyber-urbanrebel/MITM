#!/usr/bin/env bash
# setup.sh — Create virtual environment and install dependencies
set -e

VENV_DIR="venv"

echo "[*] Creating virtual environment in ./${VENV_DIR} ..."
python3 -m venv "${VENV_DIR}"

echo "[*] Activating virtual environment ..."
# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"

echo "[*] Upgrading pip ..."
pip install --upgrade pip

echo "[*] Installing dependencies ..."
pip install -r requirements.txt

echo ""
echo "[+] Setup complete!"
echo ""
echo "    Activate the environment:  source ${VENV_DIR}/bin/activate"
echo "    Run the CLI proxy:         python proxy.py"
echo "    Run the web UI proxy:      python webui.py"
echo ""
echo "    On first run, mitmproxy generates a CA certificate in ~/.mitmproxy/"
echo "    Install ~/.mitmproxy/mitmproxy-ca-cert.pem in your browser / OS"
echo "    trust store so HTTPS traffic can be intercepted."
