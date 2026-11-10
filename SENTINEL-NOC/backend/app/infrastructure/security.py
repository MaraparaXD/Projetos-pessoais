import hashlib
import hmac
import re
import secrets
import time

from cryptography.fernet import Fernet
from fastapi import HTTPException
from pwdlib import PasswordHash

from app.core.config import get_settings

password_hasher = PasswordHash.recommended()
DUMMY_HASH = password_hasher.hash(secrets.token_urlsafe(24))


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def secret_cipher():
    key = get_settings().integration_encryption_key
    if not key:
        raise HTTPException(503, "Configure INTEGRATION_ENCRYPTION_KEY before creating integrations")
    return Fernet(key.encode())


def encrypt_secret(secret: str) -> str:
    return secret_cipher().encrypt(secret.encode()).decode()


def decrypt_secret(secret: str) -> str:
    return secret_cipher().decrypt(secret.encode()).decode()


def verify_signature(secret: str, body: bytes, timestamp: str, signature: str):
    if not timestamp.isdigit() or len(timestamp) > 12:
        raise HTTPException(401, "Invalid webhook authentication")
    if abs(time.time() - int(timestamp)) > get_settings().webhook_clock_skew_seconds:
        raise HTTPException(401, "Expired webhook signature")
    expected = (
        "sha256=" + hmac.new(secret.encode(), timestamp.encode() + b"." + body, hashlib.sha256).hexdigest()
    )
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(401, "Invalid webhook authentication")


def redact_output(output: str) -> str:

    return re.sub(
        r"(?i)\b(password|passwd|token|secret|authorization|api[_-]?key)\s*[:=]\s*[^\s,;]+",
        r"\1=[REDACTED]",
        output,
    )
