from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Ticket, TicketComment
from .permissions import IsOwnerOrEngineer
from .serializers import (
    TicketCommentSerializer,
    TicketCreateSerializer,
    TicketSerializer,
    TicketUpdateSerializer,
)


class TicketViewSet(viewsets.ModelViewSet):
    """CRUD API for tickets.

    GET    /api/tickets/             - list (filtered by role, see below)
    POST   /api/tickets/             - create a new ticket (auto-routed by ML)
    GET    /api/tickets/{id}/        - retrieve
    PATCH  /api/tickets/{id}/        - update status/assignment (engineers)
    DELETE /api/tickets/{id}/        - delete (engineers/admins)
    POST   /api/tickets/{id}/comments/ - add a comment to a ticket
    GET    /api/tickets/{id}/comments/ - list a ticket's comments

    Supports filtering via query params, e.g.:
        /api/tickets/?status=OPEN
        /api/tickets/?priority=CRITICAL
        /api/tickets/?assigned_team=NETWORK
    """

    permission_classes = [permissions.IsAuthenticated, IsOwnerOrEngineer]
    filterset_fields = ["status", "priority", "assigned_team"]

    def get_queryset(self):
        user = self.request.user
        queryset = Ticket.objects.select_related("created_by", "assigned_to").prefetch_related(
            "comments__author"
        )

        if user.is_engineer:
            # Engineers/admins see everything, but engineers without an
            # ADMIN role only see tickets routed to their own team plus
            # tickets they personally created.
            if user.role == user.Role.ENGINEER and user.team:
                from django.db.models import Q

                return queryset.filter(
                    Q(assigned_team=user.team) | Q(created_by=user)
                )
            return queryset

        # Regular end users only see their own tickets.
        return queryset.filter(created_by=user)

    def get_serializer_class(self):
        if self.action == "create":
            return TicketCreateSerializer
        if self.action in ("update", "partial_update"):
            return TicketUpdateSerializer
        return TicketSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = TicketSerializer(instance)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        # Run the (partial) update with the slim update serializer, then
        # return the full representation so the client always gets the
        # nested created_by/assigned_to/comments fields back.
        super().update(request, *args, **kwargs)
        instance = self.get_object()
        return Response(TicketSerializer(instance).data)

    @action(detail=True, methods=["get", "post"], url_path="comments")
    def comments(self, request, pk=None):
        ticket = self.get_object()

        if request.method == "GET":
            serializer = TicketCommentSerializer(ticket.comments.all(), many=True)
            return Response(serializer.data)

        serializer = TicketCommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(ticket=ticket, author=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
