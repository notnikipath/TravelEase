from __future__ import annotations

import base64
import hashlib
import hmac
import json
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any


class Role(str, Enum):
    CUSTOMER = "customer"
    MANAGER = "manager"
    HOTELIER = "hotelier"
    ADMIN = "admin"


PERMISSIONS: dict[Role, set[str]] = {
    Role.CUSTOMER: {"search:read", "booking:create", "booking:read", "review:create", "loyalty:read"},
    Role.MANAGER: {"search:read", "booking:read", "booking:update", "content:update", "analytics:read"},
    Role.HOTELIER: {"content:update", "analytics:read"},
    Role.ADMIN: {
        "search:read",
        "booking:create",
        "booking:read",
        "booking:update",
        "content:update",
        "review:create",
        "analytics:read",
        "loyalty:read",
        "loyalty:update",
    },
}


def has_permission(role: Role, action: str) -> bool:
    return action in PERMISSIONS.get(role, set())


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64decode(data: str) -> bytes:
    padding = "=" * ((4 - len(data) % 4) % 4)
    return base64.urlsafe_b64decode(data + padding)


def sign_token(payload: dict[str, Any], secret: str, exp_minutes: int = 240) -> str:
    now = datetime.now(UTC)
    token_payload = {
        **payload,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=exp_minutes)).timestamp()),
    }
    header = {"alg": "HS256", "typ": "JWT"}
    header_b64 = _b64(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _b64(json.dumps(token_payload, separators=(",", ":")).encode("utf-8"))
    signature = hmac.new(secret.encode("utf-8"), f"{header_b64}.{payload_b64}".encode(), hashlib.sha256).digest()
    signature_b64 = _b64(signature)
    return f"{header_b64}.{payload_b64}.{signature_b64}"


def verify_token(token: str, secret: str) -> dict[str, Any] | None:
    parts = token.split(".")
    if len(parts) != 3:
        return None
    header_b64, payload_b64, signature_b64 = parts
    expected_sig = hmac.new(secret.encode("utf-8"), f"{header_b64}.{payload_b64}".encode(), hashlib.sha256).digest()
    if not hmac.compare_digest(_b64(expected_sig), signature_b64):
        return None
    try:
        payload = json.loads(_b64decode(payload_b64).decode("utf-8"))
    except (ValueError, json.JSONDecodeError):
        return None
    if int(datetime.now(UTC).timestamp()) > int(payload.get("exp", 0)):
        return None
    return payload
