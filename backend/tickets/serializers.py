from rest_framework import serializers

from users.serializers import UserSerializer

from .models import Ticket, TicketComment


class TicketCommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = TicketComment
        fields = ["id", "ticket", "author", "body", "created_at"]
        read_only_fields = ["id", "ticket", "author", "created_at"]


class TicketSerializer(serializers.ModelSerializer):
    """Full read representation of a ticket, including nested user info
    and a couple of computed/derived fields."""

    created_by = UserSerializer(read_only=True)
    assigned_to = UserSerializer(read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    comments = TicketCommentSerializer(many=True, read_only=True)

    class Meta:
        model = Ticket
        fields = [
            "id",
            "title",
            "description",
            "priority",
            "status",
            "assigned_team",
            "routed_confidence",
            "created_by",
            "assigned_to",
            "due_at",
            "is_overdue",
            "created_at",
            "updated_at",
            "resolved_at",
            "comments",
        ]
        read_only_fields = [
            "id",
            "assigned_team",
            "routed_confidence",
            "created_by",
            "due_at",
            "is_overdue",
            "created_at",
            "updated_at",
            "resolved_at",
            "comments",
        ]


class TicketCreateSerializer(serializers.ModelSerializer):
    """Slim serializer used for POST /api/tickets/.

    Only `title`, `description`, and `priority` are accepted from the
    client. `assigned_team` is filled in automatically by the ML router
    (see tickets/signals.py) and `created_by`/`due_at` are set server-side.
    """

    class Meta:
        model = Ticket
        fields = ["id", "title", "description", "priority"]
        read_only_fields = ["id"]


class TicketUpdateSerializer(serializers.ModelSerializer):
    """Used for PATCH/PUT by engineers: status, assignment, team override."""

    class Meta:
        model = Ticket
        fields = [
            "title",
            "description",
            "priority",
            "status",
            "assigned_team",
            "assigned_to",
        ]
