import pytest

from centrifugo_toolkit import client as client_module
from centrifugo_toolkit.client import CentrifugoError, get_client, publish_to_centrifugo
from centrifugo_toolkit.testing import FakeCentrifugoClient, fake_centrifugo


class TestFakeCentrifugoClient:
    def test_records_published_calls(self):
        fake = FakeCentrifugoClient()
        fake.publish("org:#1", {"type": "project_update"})

        assert fake.published == [("org:#1", {"type": "project_update"})]

    def test_records_broadcast_calls(self):
        fake = FakeCentrifugoClient()
        fake.broadcast(["org:#1", "org:#2"], {"type": "announcement"})

        assert fake.broadcasted == [(["org:#1", "org:#2"], {"type": "announcement"})]


class TestFakeCentrifugoContextManager:
    def test_swaps_and_restores_default_client(self):
        previous = client_module._default_client
        with fake_centrifugo() as fake:
            assert get_client() is fake
            publish_to_centrifugo("user:#1", {"type": "notification"})
            assert fake.published == [("user:#1", {"type": "notification"})]

        assert client_module._default_client is previous

    def test_restores_default_client_even_on_error(self):
        previous = client_module._default_client
        with pytest.raises(ValueError):
            with fake_centrifugo():
                raise ValueError("boom")

        assert client_module._default_client is previous

    def test_default_client_unset_again_after_block_if_it_was_unset_before(self):
        client_module._default_client = None
        with fake_centrifugo():
            pass

        with pytest.raises(CentrifugoError, match="not configured"):
            get_client()
