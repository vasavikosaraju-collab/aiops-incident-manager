from drf_spectacular.utils import extend_schema
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from . import classifier
from .serializers import PredictTeamRequestSerializer, PredictTeamResponseSerializer


class PredictTeamView(APIView):
    """POST /api/predict-team/

    Given a free-text ticket description, returns the support team
    predicted by the TF-IDF + Random Forest model along with a
    confidence score.

    This is the same model used internally (see
    `tickets/signals.py`) to auto-route every newly created ticket; this
    endpoint exposes it directly, e.g. for a "preview routing before you
    submit" feature in the UI, or for engineers triaging tickets that
    came in through another channel (email, Slack, etc).

    Example request:
        {"description": "VPN connection failing for remote employee"}

    Example response:
        {"team": "NETWORK", "confidence": 0.83}
    """

    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request=PredictTeamRequestSerializer,
        responses=PredictTeamResponseSerializer,
    )
    def post(self, request):
        serializer = PredictTeamRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        team, confidence = classifier.predict_team(
            serializer.validated_data["description"]
        )

        response = PredictTeamResponseSerializer(
            {"team": team, "confidence": confidence}
        )
        return Response(response.data)
