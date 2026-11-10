"""Gera credenciais locais sem sobrescrever o arquivo .env."""

import base64
import secrets
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[1]
    target = root / ".env"
    if target.exists():
        raise SystemExit(".env já existe; arquivo preservado. Consulte as credenciais locais nele.")
    values = (root / ".env.example").read_text(encoding="utf-8")
    for marker, value in {
        "CHANGE_DATABASE_PASSWORD": secrets.token_hex(24),
        "CHANGE_ADMIN_PASSWORD": secrets.token_urlsafe(24),
        "CHANGE_WEBHOOK_SECRET": secrets.token_urlsafe(48),
        "CHANGE_ENCRYPTION_KEY": base64.urlsafe_b64encode(secrets.token_bytes(32)).decode(),
    }.items():
        values = values.replace(marker, value)

    with target.open("x", encoding="utf-8", newline="\n") as file:
        file.write(values)
    try:
        target.chmod(0o600)
    except OSError:
        pass
    print(".env criado com segredos aleatórios. Login: admin@sentinel.local")
    print("Consulte BOOTSTRAP_ADMIN_PASSWORD no .env. Não compartilhe nem versione esse arquivo.")


if __name__ == "__main__":
    main()
