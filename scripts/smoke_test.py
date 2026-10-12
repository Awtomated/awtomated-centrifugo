"""Publishes a real message to a locally running Centrifugo instance (via docker-compose) to
verify centrifugo_toolkit's HTTP client actually speaks Centrifugo's current API correctly.

Unit tests mock the HTTP layer, so they can't catch a wrong URL/header/body shape against the
real server - this script is what does. Run it after `docker compose up -d`:

    CENTRIFUGO_API_URL=http://localhost:8888 \
    CENTRIFUGO_API_KEY=dev-api-key-change-me \
    python scripts/smoke_test.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import centrifugo_toolkit  # noqa: E402
from centrifugo_toolkit.channels import org_channel  # noqa: E402


def main() -> None:
    api_url = os.environ.get("CENTRIFUGO_API_URL", "http://localhost:8888")
    api_key = os.environ.get("CENTRIFUGO_API_KEY", "dev-api-key-change-me")

    centrifugo_toolkit.configure(api_url=api_url, api_key=api_key)

    channel = org_channel("smoke-test-org")
    result = centrifugo_toolkit.publish_to_centrifugo(
        channel, {"type": "smoke_test", "provider": "smoke_test_script"},
    )

    print(f"Published to {channel!r} against {api_url}")
    print(f"Response: {result}")
    # A namespace with history enabled (like "org" here) echoes back {"offset", "epoch"}
    # instead of an empty object, so assert on the absence of an error, not an exact shape.
    assert "result" in result, f"unexpected response: {result}"
    print("OK - centrifugo_toolkit successfully published to a real Centrifugo instance.")


if __name__ == "__main__":
    main()
