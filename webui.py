#!/usr/bin/env python3
"""
webui.py — Launch the MITM proxy with the mitmweb interactive web interface.

mitmweb provides a browser-based UI for real-time traffic inspection,
filtering, replaying, and modifying flows.

Usage
-----
    python webui.py [--port PORT] [--web-port WEB_PORT]
                    [--no-logger] [--no-blocker] [--no-modifier]

Examples
--------
    # Default: proxy on 8080, web UI on 8081
    python webui.py

    # Custom ports
    python webui.py --port 8888 --web-port 9000
"""

import argparse
import subprocess
import sys


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="MITM web-UI proxy (mitmweb wrapper)",
    )
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=8080,
        help="Proxy listen port (default: 8080)",
    )
    parser.add_argument(
        "--web-port", "-w",
        type=int,
        default=8081,
        dest="web_port",
        help="mitmweb HTTP interface port (default: 8081)",
    )
    parser.add_argument(
        "--no-logger",
        action="store_true",
        help="Disable the traffic logger addon",
    )
    parser.add_argument(
        "--no-blocker",
        action="store_true",
        help="Disable the URL blocker addon",
    )
    parser.add_argument(
        "--no-modifier",
        action="store_true",
        help="Disable the request/response modifier addon",
    )
    return parser.parse_args()


def build_command(args: argparse.Namespace) -> list[str]:
    cmd = [
        "mitmweb",
        "--listen-port", str(args.port),
        "--web-port", str(args.web_port),
        "--web-host", "127.0.0.1",
        "--set", "ssl_insecure=false",
    ]

    if not args.no_logger:
        cmd += ["-s", "addons/logger.py"]

    if not args.no_blocker:
        cmd += ["-s", "addons/blocker.py"]

    if not args.no_modifier:
        cmd += ["-s", "addons/modifier.py"]

    return cmd


def main() -> None:
    args = parse_args()
    cmd = build_command(args)

    print("=" * 60)
    print("  MITM Web UI Proxy")
    print("=" * 60)
    print(f"  Proxy listening on  : 0.0.0.0:{args.port}")
    print(f"  Web interface       : http://127.0.0.1:{args.web_port}")
    print(f"  Logger              : {'disabled' if args.no_logger else 'enabled → logs/traffic.log'}")
    print(f"  Blocker             : {'disabled' if args.no_blocker else 'enabled'}")
    print(f"  Modifier            : {'disabled' if args.no_modifier else 'enabled'}")
    print()
    print("  Configure your browser/device to use this machine as an HTTP/HTTPS proxy.")
    print(f"  Proxy address: <your-ip>:{args.port}")
    print()
    print("  CA certificate: ~/.mitmproxy/mitmproxy-ca-cert.pem")
    print("  Install it in your browser/OS trust store to intercept HTTPS.")
    print()
    print(f"  Open http://127.0.0.1:{args.web_port} in your browser to view live traffic.")
    print()
    print("  Press Ctrl+C to stop.")
    print("=" * 60)
    print()

    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n[*] Proxy stopped.")
    except FileNotFoundError:
        print(
            "\n[!] 'mitmweb' not found.\n"
            "    Activate the virtual environment and run setup.sh first:\n"
            "        source venv/bin/activate\n"
            "        bash setup.sh\n",
            file=sys.stderr,
        )
        sys.exit(1)
    except subprocess.CalledProcessError as exc:
        sys.exit(exc.returncode)


if __name__ == "__main__":
    main()
