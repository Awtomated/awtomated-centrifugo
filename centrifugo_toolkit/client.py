from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from typing import Any, List, Mapping, Optional

import requests

logger = logging.getLogger("centrifugo_toolkit")


class CentrifugoError(Exception):
    """Raised when a Centrifugo API call fails after all retries."""


@dataclass
class CentrifugoConfig:
    api_url: str
    api_key: str
    timeout: float = 5.0
    max_retries: int = 2
    retry_backoff: float = 0.5


class CentrifugoClient:
    """Thin HTTP client for Centrifugo's server API (https://centrifugal.dev/docs/server/server_api)."""

    def __init__(self, config: CentrifugoConfig, session: Optional[requests.Session] = None):
        self._config = config
        self._session = session or requests.Session()

    def publish(self, channel: str, data: Mapping[str, Any]) -> dict:
        """Publish `data` to a single channel. Every subscriber receives it immediately."""
        return self._call("publish", {"channel": channel, "data": data})

    def broadcast(self, channels: List[str], data: Mapping[str, Any]) -> dict:
        """Publish the same `data` to several channels in one API call."""
        return self._call("broadcast", {"channels": channels, "data": data})

    def _call(self, method: str, body: Mapping[str, Any]) -> dict:
        # Every Centrifugo HTTP API method has its own path (/api/publish, /api/broadcast, ...)
        # and takes its params as the top-level JSON body - there is no single /api endpoint
        # with a {"method", "params"} envelope. Auth is the X-API-Key header, not Authorization.
        # https://centrifugal.dev/docs/server/server_api
        url = f"{self._config.api_url.rstrip('/')}/api/{method}"
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": self._config.api_key,
        }
        last_exc: Optional[Exception] = None
        for attempt in range(self._config.max_retries + 1):
            try:
                response = self._session.post(
                    url, data=json.dumps(body), headers=headers, timeout=self._config.timeout,
                )
                response.raise_for_status()
                body = response.json()
                if body.get("error"):
                    # Centrifugo accepted the request and rejected it deterministically
                    # (bad channel name, bad payload, ...) - retrying the same call won't
                    # help, so surface the real error instead of masking it after N retries.
                    raise CentrifugoError(f"Centrifugo API error: {body['error']}")
                return body
            except (requests.RequestException, ValueError) as exc:
                last_exc = exc
                logger.warning(
                    "centrifugo_toolkit: %s attempt %s/%s failed: %s",
                    method, attempt + 1, self._config.max_retries + 1, exc,
                )
                if attempt < self._config.max_retries:
                    time.sleep(self._config.retry_backoff * (2 ** attempt))

        raise CentrifugoError(
            f"Centrifugo {method} failed after {self._config.max_retries + 1} attempt(s)"
        ) from last_exc


_default_client: Optional[CentrifugoClient] = None


def configure(api_url: str, api_key: str, timeout: float = 5.0, max_retries: int = 2) -> CentrifugoClient:
    """Set up the module-level default client. Call once at process startup."""
    global _default_client
    _default_client = CentrifugoClient(
        CentrifugoConfig(api_url=api_url, api_key=api_key, timeout=timeout, max_retries=max_retries)
    )
    return _default_client


def get_client() -> CentrifugoClient:
    if _default_client is None:
        raise CentrifugoError(
            "centrifugo_toolkit is not configured. Call centrifugo_toolkit.configure(api_url=..., "
            "api_key=...) at startup, or add 'centrifugo_toolkit.django_app' to INSTALLED_APPS "
            "with the required settings."
        )
    return _default_client


def publish_to_centrifugo(channel: str, data: Mapping[str, Any]) -> dict:
    """Convenience wrapper around the default client's `publish`."""
    return get_client().publish(channel, data)
