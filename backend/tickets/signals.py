"""
Signal handlers for the `tickets` app.

When a new ticket is created:
  1. Run it through the ML ticket-routing model (`ml_router.classifier`)
     to set `assigned_team` and `routed_confidence`.
  2. If the ticket is CRITICAL priority, create `Notification` records
     for every engineer on the assigned team and push a real-time alert
     over the `team_<team>` WebSocket group via Django Channels.

We use `Ticket.objects.filter(pk=...).update(...)` rather than
`instance.save()` to apply the routing result. This updates the row
directly without re-triggering `post_save` (avoiding infinite recursion)
and without re-running the model's custom `save()` SLA logic a second
time.
"""

import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models.signals import post_save
from django.dispatch import receiver

from ml_router import classifier
from .models import Ticket

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Ticket)
def route_and_notify(sender, instance, created, **kwargs):
    if not created:
        return

    team, confidence = classifier.predict_team(instance.description)

    if team:
        Ticket.objects.filter(pk=instance.pk).update(
            assigned_team=team, routed_confidence=confidence
        )
        instance.assigned_team = team
        instance.routed_confidence = confidence

    if instance.priority == Ticket.Priority.CRITICAL:
        _notify_team(instance)


def _notify_team(ticket: Ticket):
    from notifications.models import Notification
    from users.models import User

    message = (
        f"New CRITICAL ticket #{ticket.id}: '{ticket.title}'"
        + (f" routed to {ticket.assigned_team}" if ticket.assigned_team else "")
    )

    recipients = []
    if ticket.assigned_team:
        recipients = list(
            User.objects.filter(
                role__in=[User.Role.ENGINEER, User.Role.ADMIN],
                team=ticket.assigned_team,
            )
        )

    Notification.objects.bulk_create(
        [
            Notification(recipient=user, ticket=ticket, message=message)
            for user in recipients
        ]
    )

    channel_layer = get_channel_layer()
    if channel_layer is None:
        return

    event = {
        "type": "incident_alert",
        "ticket_id": ticket.id,
        "title": ticket.title,
        "priority": ticket.priority,
        "assigned_team": ticket.assigned_team,
        "message": message,
    }

    try:
        if ticket.assigned_team:
            async_to_sync(channel_layer.group_send)(
                f"team_{ticket.assigned_team}", event
            )
        for user in recipients:
            async_to_sync(channel_layer.group_send)(f"user_{user.id}", event)
    except Exception:  # pragma: no cover - channel layer may be unavailable in tests
        logger.exception("Failed to push real-time notification for ticket %s", ticket.id)
