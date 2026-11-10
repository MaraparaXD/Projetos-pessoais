#!/usr/bin/env python3
# SENTINEL NOC webhook notification
"""Encaminha notificações Checkmk com assinatura HMAC."""

import hashlib
import os
from datetime import UTC, datetime
from urllib.request import Request, urlopen

try:
    from scripts.simulate_checkmk import signed_payload
except ModuleNotFoundError:
    from simulate_checkmk import signed_payload


def normalize(environ):
    context = environ.get("NOTIFY_WHAT", "")
    if context not in {"HOST", "SERVICE"}:
        raise ValueError("NOTIFY_WHAT must be HOST or SERVICE")
    notification_type = environ.get("NOTIFY_NOTIFICATIONTYPE", "PROBLEM")
    if notification_type not in {"PROBLEM", "RECOVERY", "FLAPPINGSTART", "FLAPPINGSTOP"}:
        raise ValueError("Unsupported notification type; configure rule for problem/recovery/flapping only")
    raw_state = environ.get(f"NOTIFY_{context}STATE", "UNKNOWN")
    state = {"UP": "OK", "DOWN": "CRIT", "UNREACHABLE": "UNKNOWN", "WARNING": "WARN", "CRITICAL": "CRIT"}.get(
        raw_state, raw_state
    )
    if notification_type == "RECOVERY":
        state = "RECOVERY"

    stamp = environ.get("NOTIFY_LONGDATETIME")
    epoch = environ.get(
        "NOTIFY_LASTSERVICESTATECHANGE" if context == "SERVICE" else "NOTIFY_LASTHOSTSTATECHANGE"
    )
    if not epoch:
        raise ValueError("A source state-change epoch is required")
    observed_at = datetime.fromtimestamp(float(epoch), UTC).isoformat()
    host = environ["NOTIFY_HOSTNAME"]
    service = environ.get("NOTIFY_SERVICEDESC") if context == "SERVICE" else None
    identity = "|".join([host, service or "", raw_state, notification_type, epoch, stamp or ""])
    return {
        "external_id": hashlib.sha256(identity.encode()).hexdigest(),
        "host": host,
        "service": service,
        "event_type": context,
        "state": state,
        "output": environ.get(f"NOTIFY_{context}OUTPUT", ""),
        "observed_at": observed_at,
    }


def main():
    url = os.environ["SENTINEL_WEBHOOK_URL"]
    if not url.startswith("https://"):
        raise SystemExit("Notification forwarding requires HTTPS")
    body, headers = signed_payload(normalize(os.environ), os.environ["SENTINEL_WEBHOOK_SECRET"])

    with urlopen(Request(url, body, headers, method="POST"), timeout=15) as response:
        if response.status not in {200, 201}:
            raise SystemExit(f"SENTINEL HTTP {response.status}")


if __name__ == "__main__":
    main()
