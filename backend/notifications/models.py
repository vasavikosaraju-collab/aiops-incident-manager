from django.conf import settings
from django.db import models


class Notification(models.Model):
    """A real-time alert generated for a support engineer.

    Notifications are created by `tickets.signals` whenever a CRITICAL
    ticket is created or routed to a team, and pushed to connected
    clients over a WebSocket via Django Channels (see
    `notifications/consumers.py`). They are also persisted here so a
    user can see their notification history even if they were offline
    when the alert was sent.
    """

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    ticket = models.ForeignKey(
        "tickets.Ticket",
        on_delete=models.CASCADE,
        related_name="notifications",
        null=True,
        blank=True,
    )
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Notification to {self.recipient} - {self.message}"
