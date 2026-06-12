from rest_framework import serializers

from tickets.models import Ticket


class PredictTeamRequestSerializer(serializers.Serializer):
    description = serializers.CharField(
        max_length=5000,
        help_text="Free-text description of the issue, e.g. "
        "'VPN connection failing for remote employee'.",
    )


class PredictTeamResponseSerializer(serializers.Serializer):
    team = serializers.ChoiceField(
        choices=Ticket.Team.choices, allow_null=True
    )
    confidence = serializers.FloatField(allow_null=True)
