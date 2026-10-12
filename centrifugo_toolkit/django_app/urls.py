from django.urls import path

from .views import CentrifugoTokenView

urlpatterns = [
    path("token/", CentrifugoTokenView.as_view(), name="centrifugo-token"),
]
