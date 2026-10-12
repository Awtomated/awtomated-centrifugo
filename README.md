# centrifugo-toolkit

Shared Centrifugo integration for TransPM Django apps: one publish helper, one connection-token
issuer, one channel-naming convention — so every app talks to Centrifugo the same way instead of
re-implementing it locally (see the `main-api` realtime architecture proposal, Section 9).

## Install

Distributed as a git-installable package — no private package index to stand up or maintain.
Always pin a tag, never a branch:

```bash
pip install "git+https://<host>/<org>/centrifugo-toolkit.git@v0.1.0#egg=centrifugo-toolkit[django]"
```

To pick up a new version, bump the tag in the pinning repo's `requirements.txt` and reinstall.

The `django` extra pulls in `Django` and `djangorestframework`, needed only for the
`centrifugo_toolkit.django_app` integration. The core package (`client`, `auth`, `channels`,
`testing`) has no framework dependency.

## Configure (Django)

1. Add the app and required settings:

    ```python
    INSTALLED_APPS = [
        ...,
        "centrifugo_toolkit.django_app",
    ]

    CENTRIFUGO_API_URL = env("CENTRIFUGO_API_URL")              # e.g. http://centrifugo:8000
    CENTRIFUGO_API_KEY = env("CENTRIFUGO_API_KEY")               # server-side publish key
    CENTRIFUGO_TOKEN_HMAC_SECRET = env("CENTRIFUGO_TOKEN_HMAC_SECRET")
    CENTRIFUGO_TOKEN_TTL_SECONDS = 300                            # optional, defaults to 300
    CENTRIFUGO_TIMEOUT = 5.0                                      # optional, defaults to 5.0
    CENTRIFUGO_MAX_RETRIES = 2                                    # optional, defaults to 2
    ```

   `AppConfig.ready()` validates these at startup and raises `ImproperlyConfigured` immediately
   if any required setting is missing — it fails at boot, not on the first publish call.

2. Wire the connection-token endpoint into your URLconf:

    ```python
    urlpatterns = [
        path("realtime/", include("centrifugo_toolkit.django_app.urls")),
    ]
    ```

   This exposes `GET /realtime/token/`, returning `{"token": "..."}` for the authenticated user.

3. For any private channel (a project or org room), subclass the subscribe-proxy base view —
   only your app knows its own membership rules:

    ```python
    from centrifugo_toolkit.django_app.views import BaseCentrifugoSubscribeProxyView

    class ProjectSubscribeProxyView(BaseCentrifugoSubscribeProxyView):
        def is_authorized(self, request, channel: str) -> bool:
            project_id = channel.removeprefix("project:#")
            return Project.objects.filter(
                id=project_id, organization=request.user.organization,
            ).exists()
    ```

   Point Centrifugo's `proxy_subscribe_endpoint` config at this view.

## Use it

```python
from centrifugo_toolkit import org_channel, publish_to_centrifugo

def update_project(project, **changes):
    ...
    publish_to_centrifugo(
        org_channel(project.organization_id),
        {
            "type": "project_update",
            "provider": "project_service",
            "data": {"project_id": str(project.id), "cell_data": serializer.data},
            "meta": {"organization_id": str(project.organization_id)},
        },
    )
```

Non-Django callers (scripts, Celery workers without Django settings loaded) can configure the
client explicitly instead of relying on `AppConfig.ready()`:

```python
import centrifugo_toolkit

centrifugo_toolkit.configure(api_url="http://centrifugo:8000", api_key="...")
centrifugo_toolkit.publish_to_centrifugo("org:#123", {"type": "ping"})
```

## Channel convention

| Helper              | Channel            | Scope                              |
|----------------------|---------------------|-------------------------------------|
| `org_channel(id)`     | `org:#<id>`          | Everyone in an organization          |
| `project_channel(id)` | `project:#<id>`      | Users viewing/working a project      |
| `user_channel(id)`    | `user:#<id>`         | One user, all sessions/tabs          |
| `doc_channel(id)`     | `doc:#<id>`          | Users with a document open           |

## Testing your own code

Don't hit a live Centrifugo instance in unit tests — swap in the fake client:

```python
from centrifugo_toolkit.testing import fake_centrifugo
from centrifugo_toolkit.channels import org_channel

def test_update_project_notifies_org(self):
    with fake_centrifugo() as fake:
        update_project(project, name="New name")

    channel, data = fake.published[0]
    assert channel == org_channel(project.organization_id)
    assert data["type"] == "project_update"
```

## Local development

```bash
python -m venv .venv
.venv/Scripts/activate         # .venv/bin/activate on macOS/Linux
pip install -e ".[django,test]"
pytest
```

### Running against a real Centrifugo instance

Unit tests use `centrifugo_toolkit.testing.fake_centrifugo` and never touch the network. To
sanity-check the HTTP client itself against a real server (e.g. after changing `client.py`):

```bash
docker compose up -d          # starts Centrifugo + Redis, see docker-compose.yml
CENTRIFUGO_API_URL=http://localhost:8888 \
CENTRIFUGO_API_KEY=dev-api-key-change-me \
python scripts/smoke_test.py
docker compose down
```

### Admin web UI

With the containers up, open http://localhost:8888 — log in with the password from
`docker/centrifugo-config.json`'s `admin.password` (`admin-change-me` by default). Useful for
watching channels, connections and presence while testing manually. The admin block has its own
password/secret, separate from `http_api.key` — don't reuse this config outside a local machine.

The dev config in `docker/centrifugo-config.json` has no real secrets — don't reuse it anywhere
but a local machine.

## Status

v0.1.0 — proof-of-concept package validated against one real call site in `main-api` and against
a live local Centrifugo instance via `scripts/smoke_test.py`.

**Distribution: git-installable, not a package index.** No private PyPI/registry to host or
maintain — consumers pin a git tag. Revisit only if/when a second consuming repo makes tag-based
installs genuinely painful.
