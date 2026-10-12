from __future__ import annotations

import time
import uuid
from typing import Any, Mapping, Optional

import jwt

DEFAULT_TTL_SECONDS = 300


def issue_connection_token(
    user_id: str,
    hmac_secret: str,
    ttl_seconds: int = DEFAULT_TTL_SECONDS,
    extra_claims: Optional[Mapping[str, Any]] = None,
) -> str:
    """Sign a short-lived JWT a browser uses to open its Centrifugo WebSocket connection."""
    now = int(time.time())
    claims = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + ttl_seconds,
        "jti": uuid.uuid4().hex,
    }
    if extra_claims:
        claims.update(extra_claims)
    return jwt.encode(claims, hmac_secret, algorithm="HS256")


def issue_subscription_token(
    user_id: str,
    channel: str,
    hmac_secret: str,
    ttl_seconds: int = DEFAULT_TTL_SECONDS,
) -> str:
    """Sign a short-lived JWT authorizing a subscription to one private channel."""
    now = int(time.time())
    claims = {
        "sub": str(user_id),
        "channel": channel,
        "iat": now,
        "exp": now + ttl_seconds,
    }
    return jwt.encode(claims, hmac_secret, algorithm="HS256")


def decode_token(token: str, hmac_secret: str) -> dict:
    """Decode and verify a token issued by this module. Raises jwt.PyJWTError on failure."""
    return jwt.decode(token, hmac_secret, algorithms=["HS256"])
