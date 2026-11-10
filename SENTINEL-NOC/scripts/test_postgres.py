"""Executa a suíte em um banco PostgreSQL de testes isolado."""

import os
import re
import subprocess
from pathlib import Path
from urllib.parse import quote

try:
    from scripts.local_env import load_local_env
except ModuleNotFoundError:
    from local_env import load_local_env


def main():
    load_local_env()
    root = Path(__file__).resolve().parents[1]
    database = os.environ.get("POSTGRES_DB", "sentinel") + "_test"
    user = os.environ.get("POSTGRES_USER", "sentinel")
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,55}", database):
        raise SystemExit("Use a simple PostgreSQL database name for this test helper")
    password = os.environ.get("POSTGRES_PASSWORD")
    if not password:
        raise SystemExit("Generate the local .env before running PostgreSQL tests")
    exists = subprocess.run(
        [
            "docker",
            "compose",
            "exec",
            "-T",
            "db",
            "psql",
            "-U",
            user,
            "-d",
            "postgres",
            "-tAc",
            f"SELECT 1 FROM pg_database WHERE datname='{database}'",
        ],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if exists != "1":
        subprocess.run(
            ["docker", "compose", "exec", "-T", "db", "createdb", "-U", user, database], cwd=root, check=True
        )
    env = os.environ.copy()
    env["TEST_DATABASE_URL"] = (
        f"postgresql+psycopg://{quote(user, safe='')}:{quote(password, safe='')}@db:5432/{database}"
    )

    args = [
        "docker",
        "compose",
        "run",
        "--rm",
        "--no-deps",
        "--user",
        "root",
        "-e",
        "TEST_DATABASE_URL",
        "-e",
        "PYTHONPATH=/app:/workspace",
        "-v",
        f"{root / 'backend' / 'tests'}:/app/tests:ro",
        "-v",
        f"{root / 'scripts'}:/workspace/scripts:ro",
        "-v",
        f"{root / 'backend' / 'requirements-dev.lock'}:/tmp/requirements-dev.lock:ro",
        "api",
        "sh",
        "-c",
        "pip install --disable-pip-version-check -q -r /tmp/requirements-dev.lock && python -m pytest -q",
    ]
    print(f"Testing disposable database {database}; demo database is preserved", flush=True)
    subprocess.run(args, cwd=root, env=env, check=True)


if __name__ == "__main__":
    main()
