"""Test doubles for consuming apps. Import these in your own tests instead of hitting a live
Centrifugo instance.

    from centrifugo_toolkit.testing import fake_centrifugo

    def test_project_update_notifies_org(self):
        with fake_centrifugo() as fake:
            update_project(project, name="New name")
            channel, data = fake.published[0]
            assert channel == org_channel(project.organization_id)
            assert data["type"] == "project_update"
"""
from __future__ import annotations

import contextlib
from typing import Any, List, Mapping, Tuple

from . import client as _client_module


class FakeCentrifugoClient:
    """Drop-in replacement for CentrifugoClient that records calls instead of making HTTP requests."""

    def __init__(self):
        self.published: List[Tuple[str, Mapping[str, Any]]] = []
        self.broadcasted: List[Tuple[List[str], Mapping[str, Any]]] = []

    def publish(self, channel: str, data: Mapping[str, Any]) -> dict:
        self.published.append((channel, data))
        return {"result": {}}

    def broadcast(self, channels: List[str], data: Mapping[str, Any]) -> dict:
        self.broadcasted.append((list(channels), data))
        return {"result": {}}


@contextlib.contextmanager
def fake_centrifugo():
    """Swap the module-level default client for a FakeCentrifugoClient for the duration of a `with` block."""
    fake = FakeCentrifugoClient()
    previous = _client_module._default_client
    _client_module._default_client = fake
    try:
        yield fake
    finally:
        _client_module._default_client = previous
