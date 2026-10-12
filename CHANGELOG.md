# Changelog

All notable changes to this project are documented here.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.1.0] - Unreleased

### Added
- `CentrifugoClient` / `publish_to_centrifugo()` — HTTP publish helper with retries and timeouts.
- `issue_connection_token()` / `issue_subscription_token()` — HMAC-signed JWT issuance.
- Channel-naming helpers: `org_channel`, `project_channel`, `user_channel`, `doc_channel`.
- `centrifugo_toolkit.django_app` — AppConfig with settings validation, connection-token view,
  and a base subscribe-proxy view for private channels.
- `centrifugo_toolkit.testing` — `FakeCentrifugoClient` and `fake_centrifugo()` for consuming
  apps' unit tests.
- `docker-compose.yml` + `docker/centrifugo-config.json` — local Centrifugo + Redis for
  integration-testing the HTTP client against a real server.
- `scripts/smoke_test.py` — verifies `publish_to_centrifugo()` against a live Centrifugo instance.

### Fixed
- `CentrifugoClient` was calling a single `/api` endpoint with a `{"method", "params"}` body and
  an `Authorization: apikey ...` header — an outdated shape. Centrifugo's current HTTP API uses
  per-method paths (`/api/publish`, `/api/broadcast`) with the params as the top-level body and
  an `X-API-Key` header. Caught by running `scripts/smoke_test.py` against a real instance, not
  by the mocked unit tests.
- A deterministic Centrifugo API error (e.g. "unknown channel") was being retried and its message
  replaced by a generic "failed after N attempts" error. Non-retryable API errors now raise
  immediately with the real message; only network/timeout failures are retried.

### Distribution
- Git-installable (pin a tag), not a private package index — see README "Status".
