#!/usr/bin/env python3
"""
proxy.py — Launch the MITM proxy in command-line (mitmdump) mode.

All three addons are loaded automatically:
  • addons/logger.py   — logs every request/response to stdout + logs/traffic.log
  • addons/blocker.py  — blocks URLs that match the default (or custom) blocklist
  • addons/modifier.py — injects headers / rewrites response bodies

Usage
-----
    python proxy.py [--port PORT] [--block PATTERN] [--no-logger]
                    [--no-blocker] [--no-modifier]

Examples
--------
    # Default: port 8080, all addons enabled
    python proxy.py

    # Custom port with an extra blocking pattern
    python proxy.py --port 8888 --block "ads\.example\.com"

    # Disable the blocker
    python proxy.py --no-blocker
"""

import argparse
import subprocess
import sys


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="MITM CLI proxy (mitmdump wrapper)",
    )
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=8080,
        help="Proxy listen port (default: 8080)",
    )
    parser.add_argument(
        "--block",
        metavar="PATTERN",
        default="",
        help="Extra comma-separated regex patterns to block (appended to defaults)",
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
        "mitmdump",
        "--listen-port", str(args.port),
        "--set", "ssl_insecure=false",
    ]

    if not args.no_logger:
        cmd += ["-s", "addons/logger.py"]

    if not args.no_blocker:
        cmd += ["-s", "addons/blocker.py"]
        if args.block:
            cmd += ["--set", f"block_patterns={args.block}"]

    if not args.no_modifier:
        cmd += ["-s", "addons/modifier.py"]

    return cmd


def main() -> None:
    args = parse_args()
    cmd = build_command(args)

    print("=" * 60)
    print("  MITM CLI Proxy")
    print("=" * 60)
    print(f"  Listening on : 0.0.0.0:{args.port}")
    print(f"  Logger       : {'disabled' if args.no_logger else 'enabled → logs/traffic.log'}")
    print(f"  Blocker      : {'disabled' if args.no_blocker else 'enabled'}")
    print(f"  Modifier     : {'disabled' if args.no_modifier else 'enabled'}")
    print()
    print("  Configure your browser/device to use this machine as an HTTP/HTTPS proxy.")
    print(f"  Proxy address: <your-ip>:{args.port}")
    print()
    print("  CA certificate: ~/.mitmproxy/mitmproxy-ca-cert.pem")
    print("  Install it in your browser/OS trust store to intercept HTTPS.")
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
            "\n[!] 'mitmdump' not found.\n"
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
