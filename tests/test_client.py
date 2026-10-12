from unittest.mock import MagicMock, patch

import pytest
import requests

from centrifugo_toolkit import client as client_module
from centrifugo_toolkit.client import (
    CentrifugoClient,
    CentrifugoConfig,
    CentrifugoError,
    configure,
    get_client,
    publish_to_centrifugo,
)


@pytest.fixture(autouse=True)
def reset_default_client():
    """Every test starts with no default client configured."""
    previous = client_module._default_client
    client_module._default_client = None
    yield
    client_module._default_client = previous


def make_client(**overrides):
    defaults = dict(
        api_url="https://centrifugo.example.com",
        api_key="test-key",
        timeout=1.0,
        max_retries=2,
        retry_backoff=0.0,
    )
    defaults.update(overrides)
    return CentrifugoClient(CentrifugoConfig(**defaults))


def mock_response(json_body, status_ok=True):
    response = MagicMock()
    response.json.return_value = json_body
    if status_ok:
        response.raise_for_status.return_value = None
    else:
        response.raise_for_status.side_effect = requests.HTTPError("boom")
    return response


class TestPublish:
    def test_publish_success_posts_expected_payload(self):
        client = make_client()
        with patch.object(client._session, "post", return_value=mock_response({"result": {}})) as post:
            result = client.publish("org:#123", {"type": "project_update"})

        assert result == {"result": {}}
        post.assert_called_once()
        args, kwargs = post.call_args
        assert args[0] == "https://centrifugo.example.com/api/publish"
        assert kwargs["headers"]["X-API-Key"] == "test-key"
        assert "org:#123" in kwargs["data"]

    def test_publish_retries_then_succeeds(self):
        client = make_client()
        with patch.object(
            client._session, "post",
            side_effect=[requests.ConnectionError("down"), mock_response({"result": {}})],
        ) as post:
            result = client.publish("org:#123", {"type": "project_update"})

        assert result == {"result": {}}
        assert post.call_count == 2

    def test_publish_raises_after_exhausting_retries(self):
        client = make_client(max_retries=1)
        with patch.object(client._session, "post", side_effect=requests.ConnectionError("down")) as post:
            with pytest.raises(CentrifugoError):
                client.publish("org:#123", {"type": "project_update"})

        assert post.call_count == 2  # initial attempt + 1 retry

    def test_error_in_response_body_raises(self):
        client = make_client(max_retries=0)
        with patch.object(
            client._session, "post",
            return_value=mock_response({"error": {"code": 105, "message": "unknown channel"}}),
        ):
            with pytest.raises(CentrifugoError, match="unknown channel"):
                client.publish("bad:#channel", {})


class TestBroadcast:
    def test_broadcast_posts_all_channels(self):
        client = make_client()
        with patch.object(client._session, "post", return_value=mock_response({"result": {}})) as post:
            client.broadcast(["org:#1", "org:#2"], {"type": "announcement"})

        args, kwargs = post.call_args
        assert args[0] == "https://centrifugo.example.com/api/broadcast"
        assert "org:#1" in kwargs["data"] and "org:#2" in kwargs["data"]


class TestDefaultClient:
    def test_get_client_without_configure_raises(self):
        with pytest.raises(CentrifugoError, match="not configured"):
            get_client()

    def test_configure_then_publish_to_centrifugo(self):
        configure(api_url="https://centrifugo.example.com", api_key="k")
        client = get_client()
        with patch.object(client._session, "post", return_value=mock_response({"result": {}})) as post:
            publish_to_centrifugo("user:#1", {"type": "notification"})
        post.assert_called_once()
