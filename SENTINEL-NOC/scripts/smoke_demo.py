"""Verifica login, ingestão e replay na API local."""

import json
import os
import subprocess
import sys
from pathlib import Path
from urllib.request import Request, urlopen

try:
    from scripts.local_env import load_local_env
except ModuleNotFoundError:
    from local_env import load_local_env


def main():
    load_local_env()
    root = Path(__file__).resolve().parents[1]
    token = None

    def call(path, data=None, method=None):
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        request = Request(
            "http://127.0.0.1:8000" + path,
            json.dumps(data).encode() if data is not None else None,
            headers,
            method=method or ("POST" if data is not None else "GET"),
        )
        with urlopen(request, timeout=15) as response:
            return json.loads(response.read()) if response.status != 204 else None

    login = call(
        "/api/auth/login",
        {"email": os.environ["BOOTSTRAP_ADMIN_EMAIL"], "password": os.environ["BOOTSTRAP_ADMIN_PASSWORD"]},
    )
    token = login["access_token"]
    try:
        integrations = call("/api/integrations")
        integration = next(i for i in integrations if i["name"] == "Laboratório Checkmk")
        before = call("/api/dashboard")["total_events"]
        saved = root / "output" / "demo.json"
        subprocess.run(
            [
                sys.executable,
                str(root / "scripts" / "simulate_checkmk.py"),
                "--integration",
                integration["id"],
                "--save",
                str(saved),
            ],
            cwd=root,
            check=True,
        )
        after = call("/api/dashboard")["total_events"]
        if after != before + 6:
            raise RuntimeError("Expected exactly six new events from the demo")
        subprocess.run(
            [
                sys.executable,
                str(root / "scripts" / "simulate_checkmk.py"),
                "--integration",
                integration["id"],
                "--replay",
                str(saved),
            ],
            cwd=root,
            check=True,
        )
        if call("/api/dashboard")["total_events"] != after:
            raise RuntimeError("Replay unexpectedly changed the event count")
        print("Compose smoke passed: login, six persisted events, exact replay and dashboard")
        print(f"Local integration ID: {integration['id']}")
    finally:
        call("/api/auth/logout", method="POST")


if __name__ == "__main__":
    main()
