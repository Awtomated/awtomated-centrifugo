from django.conf import settings
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from centrifugo_toolkit.auth import issue_connection_token


class CentrifugoTokenView(APIView):
    """Issues a short-lived Centrifugo connection token for the authenticated user.

    Wire it into your app's urls.py:
        path("realtime/token/", CentrifugoTokenView.as_view())
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        token = issue_connection_token(
            user_id=str(request.user.id),
            hmac_secret=settings.CENTRIFUGO_TOKEN_HMAC_SECRET,
            ttl_seconds=getattr(settings, "CENTRIFUGO_TOKEN_TTL_SECONDS", 300),
        )
        return Response({"token": token})


class BaseCentrifugoSubscribeProxyView(APIView):
    """Base view for Centrifugo's subscribe proxy (https://centrifugal.dev/docs/server/proxy).

    Each app that has private channels (e.g. project or org rooms) subclasses this and
    implements `is_authorized`, since only that app knows its own membership rules.

        class ProjectSubscribeProxyView(BaseCentrifugoSubscribeProxyView):
            def is_authorized(self, request, channel: str) -> bool:
                project_id = channel.removeprefix("project:#")
                return Project.objects.filter(
                    id=project_id, organization=request.user.organization,
                ).exists()
    """

    permission_classes = [IsAuthenticated]

    def is_authorized(self, request, channel: str) -> bool:
        raise NotImplementedError

    def post(self, request):
        channel = request.data.get("channel", "")
        if not self.is_authorized(request, channel):
            return Response({"error": {"code": 403, "message": "unauthorized"}})
        return Response({"result": {}})
