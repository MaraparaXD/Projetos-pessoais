"""Envia eventos sintéticos compatíveis com o contrato Checkmk."""

import argparse
import hashlib
import hmac
import json
import os
import time
import uuid
from datetime import UTC, datetime, timedelta
from urllib.error import HTTPError
from urllib.request import Request, urlopen

try:
    from scripts.local_env import load_local_env
except ModuleNotFoundError:
    from local_env import load_local_env


def signed_payload(payload, secret, timestamp=None):
    body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode()
    stamp = str(timestamp if timestamp is not None else int(time.time()))
    signature = hmac.new(secret.encode(), stamp.encode() + b"." + body, hashlib.sha256).hexdigest()
    return body, {
        "Content-Type": "application/json",
        "X-Sentinel-Timestamp": stamp,
        "X-Sentinel-Signature": "sha256=" + signature,
    }


def scenario(name="demo", run_id=None):
    run = run_id or uuid.uuid4().hex[:12]
    start = datetime.now(UTC) - timedelta(seconds=1 if name == "recovery" else 60)
    rows = [
        ("lab-edge-01", None, "CRIT", "Host sem resposta ICMP — cenário sintético"),
        ("lab-db-01", "PostgreSQL connections", "WARN", "Conexões em 82% do limite — sintético"),
        ("lab-web-01", "HTTP health", "CRIT", "HTTP 503 no endpoint de saúde — sintético"),
        ("lab-vpn-01", "OpenVPN tunnel", "UNKNOWN", "Estado do túnel indisponível — sintético"),
        ("lab-db-01", "Disk /var", "CRIT", "Uso em 96% — sintético"),
        ("lab-web-02", "HTTP health", "WARN", "Latência acima de 900 ms — sintético"),
    ]
    if name == "flapping":
        rows = [
            ("lab-flap-01", "Link", state, "Oscilação sintética")
            for state in ["CRIT", "OK", "CRIT", "OK", "CRIT", "OK", "CRIT"]
        ]
    elif name == "recovery":
        rows = [
            ("lab-edge-01", None, "RECOVERY", "Disponibilidade restaurada — sintético"),
            ("lab-web-01", "HTTP health", "OK", "HTTP 200 — sintético"),
        ]
    result = [
        {
            "external_id": f"{run}-{i}",
            "host": host,
            "service": service,
            "event_type": "SERVICE" if service else "HOST",
            "state": state,
            "output": output,
            "observed_at": (start + timedelta(seconds=i)).isoformat(),
        }
        for i, (host, service, state, output) in enumerate(rows)
    ]
    if name == "demo":
        result.append(result[0].copy())
    return result


def main():
    load_local_env()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--integration", required=True, help="Integration UUID from panel or API")
    parser.add_argument("--scenario", choices=["demo", "flapping", "recovery"], default="demo")
    parser.add_argument(
        "--run-id", help="Reuse to test replay; timestamp must also match (see --save/--replay)"
    )
    parser.add_argument("--save", help="Save generated synthetic payloads for exact replay")
    parser.add_argument("--replay", help="Replay previously saved payloads with fresh transport signatures")
    args = parser.parse_args()
    secret = os.getenv("SENTINEL_WEBHOOK_SECRET") or os.getenv("BOOTSTRAP_WEBHOOK_SECRET")
    if not secret:
        parser.error("Set SENTINEL_WEBHOOK_SECRET (or generate local .env)")
    from pathlib import Path

    payloads = (
        json.loads(Path(args.replay).read_text(encoding="utf-8"))
        if args.replay
        else scenario(args.scenario, args.run_id)
    )
    if args.save:
        Path(args.save).parent.mkdir(parents=True, exist_ok=True)
        Path(args.save).write_text(json.dumps(payloads, ensure_ascii=False, indent=2), encoding="utf-8")
    for payload in payloads:
        body, headers = signed_payload(payload, secret)
        request = Request(
            f"{args.url.rstrip('/')}/api/webhooks/checkmk/{args.integration}", body, headers, method="POST"
        )
        try:
            with urlopen(request, timeout=15) as response:
                result = json.load(response)
                print(
                    f"{response.status} {payload['host']} {payload['state']} duplicate={result['duplicate']}"
                )
        except HTTPError as exc:
            raise SystemExit(f"HTTP {exc.code}: {exc.read(500).decode()}") from None


if __name__ == "__main__":
    main()
