from django.conf import settings
from django.db import models
from django.utils import timezone


class Ticket(models.Model):
    """An IT support ticket / incident.

    `assigned_team` is populated automatically when a ticket is created
    (see tickets/signals.py), using the ML classifier in `ml_router`.
    Engineers/admins can override it manually via the API.
    """

    class Priority(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"
        CRITICAL = "CRITICAL", "Critical"

    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        RESOLVED = "RESOLVED", "Resolved"
        CLOSED = "CLOSED", "Closed"

    class Team(models.TextChoices):
        NETWORK = "NETWORK", "Network"
        DATABASE = "DATABASE", "Database"
        SECURITY = "SECURITY", "Security"
        CLOUD = "CLOUD", "Cloud Infrastructure"
        APPLICATION = "APPLICATION", "Application Support"
        DEVOPS = "DEVOPS", "DevOps"

    # SLA response targets (in hours), keyed by priority. Used to compute
    # `due_at` when a ticket is created.
    SLA_HOURS = {
        Priority.CRITICAL: 2,
        Priority.HIGH: 8,
        Priority.MEDIUM: 24,
        Priority.LOW: 72,
    }

    title = models.CharField(max_length=255)
    description = models.TextField()

    priority = models.CharField(
        max_length=20, choices=Priority.choices, default=Priority.MEDIUM
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.OPEN
    )

    assigned_team = models.CharField(
        max_length=30, choices=Team.choices, blank=True, null=True
    )
    routed_confidence = models.FloatField(
        null=True,
        blank=True,
        help_text="Confidence score (0-1) from the ML routing model for "
        "the predicted team, if it was auto-assigned.",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tickets_created",
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tickets_assigned",
    )

    due_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"#{self.pk} {self.title} [{self.priority}/{self.status}]"

    def save(self, *args, **kwargs):
        is_new = self._state.adding

        if is_new and self.due_at is None:
            hours = self.SLA_HOURS.get(self.priority, 24)
            self.due_at = timezone.now() + timezone.timedelta(hours=hours)

        if self.status == self.Status.RESOLVED and self.resolved_at is None:
            self.resolved_at = timezone.now()
        elif self.status != self.Status.RESOLVED:
            self.resolved_at = None

        super().save(*args, **kwargs)

    @property
    def is_overdue(self):
        if self.due_at is None or self.status in (
            self.Status.RESOLVED,
            self.Status.CLOSED,
        ):
            return False
        return timezone.now() > self.due_at


class TicketComment(models.Model):
    """A free-text update/comment on a ticket, e.g. engineer notes."""

    ticket = models.ForeignKey(
        Ticket, on_delete=models.CASCADE, related_name="comments"
    )
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Comment by {self.author} on ticket #{self.ticket_id}"
