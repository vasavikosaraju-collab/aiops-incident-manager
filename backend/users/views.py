from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import User
from .serializers import RegisterSerializer, UserSerializer


class RegisterView(generics.CreateAPIView):
    """POST /api/auth/register/

    Creates a new user account. Open to anyone (no auth required) so
    new users can self-register; returns the created user (without the
    password). Clients then call /api/auth/token/ to obtain a JWT pair.
    """

    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class MeView(APIView):
    """GET /api/auth/me/

    Returns the profile of the currently authenticated user. Useful for
    the frontend to know the user's role/team after login so it can
    show/hide engineer-only actions.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
