from rest_framework import mixins, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Notification
from .serializers import NotificationSerializer


class NotificationViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Read-only history of in-app notifications for the current user.

    GET   /api/notifications/                 - list my notifications
    POST  /api/notifications/{id}/mark-read/  - mark one as read

    Real-time delivery happens separately over the
    `ws/notifications/` WebSocket (see notifications/consumers.py); this
    REST endpoint exists so the UI can show notification history and
    unread counts after the user logs back in.
    """

    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)

    @action(detail=True, methods=["post"], url_path="mark-read")
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save(update_fields=["is_read"])
        return Response(NotificationSerializer(notification).data)
