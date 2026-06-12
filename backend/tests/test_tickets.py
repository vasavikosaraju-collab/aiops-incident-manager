import pytest
from django.urls import reverse
from rest_framework import status

from tickets.models import Ticket


@pytest.mark.django_db
def test_create_ticket_is_auto_routed_by_ml_model(auth_client, end_user):
    client = auth_client(end_user)

    response = client.post(
        reverse("ticket-list"),
        {
            "title": "Cannot connect to VPN",
            "description": "VPN connection failing for remote employee",
            "priority": "HIGH",
        },
    )

    assert response.status_code == status.HTTP_201_CREATED

    ticket = Ticket.objects.get(pk=response.data["id"])
    assert ticket.created_by == end_user
    # The trained model should route VPN-related issues to NETWORK.
    assert ticket.assigned_team == "NETWORK"
    assert ticket.routed_confidence is not None
    assert 0 <= ticket.routed_confidence <= 1
    # SLA due date is set automatically based on priority.
    assert ticket.due_at is not None


@pytest.mark.django_db
def test_end_user_only_sees_their_own_tickets(auth_client, end_user, network_engineer):
    client = auth_client(end_user)
    client.post(
        reverse("ticket-list"),
        {
            "title": "My VPN is down",
            "description": "VPN connection failing for remote employee",
            "priority": "MEDIUM",
        },
    )

    other_client = auth_client(network_engineer)
    other_client.post(
        reverse("ticket-list"),
        {
            "title": "Office Wi-Fi outage",
            "description": "Wi-Fi is down on the 3rd floor",
            "priority": "LOW",
        },
    )

    response = client.get(reverse("ticket-list"))
    assert response.status_code == status.HTTP_200_OK
    titles = [t["title"] for t in response.data["results"]]
    assert "My VPN is down" in titles
    assert "Office Wi-Fi outage" not in titles


@pytest.mark.django_db
def test_engineer_sees_tickets_routed_to_their_team(
    auth_client, end_user, network_engineer
):
    client = auth_client(end_user)
    response = client.post(
        reverse("ticket-list"),
        {
            "title": "VPN keeps dropping",
            "description": "VPN connection keeps dropping for the user",
            "priority": "HIGH",
        },
    )
    assert response.data.get("id")

    engineer_client = auth_client(network_engineer)
    response = engineer_client.get(reverse("ticket-list"))

    titles = [t["title"] for t in response.data["results"]]
    assert "VPN keeps dropping" in titles


@pytest.mark.django_db
def test_end_user_cannot_change_ticket_status(auth_client, end_user, admin_user):
    client = auth_client(end_user)
    response = client.post(
        reverse("ticket-list"),
        {
            "title": "App is broken",
            "description": "Application crashes on login for the user",
            "priority": "MEDIUM",
        },
    )
    ticket_id = response.data["id"]

    response = client.patch(
        reverse("ticket-detail", args=[ticket_id]), {"status": "RESOLVED"}
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN

    admin_client = auth_client(admin_user)
    response = admin_client.patch(
        reverse("ticket-detail", args=[ticket_id]), {"status": "RESOLVED"}
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.data["status"] == "RESOLVED"
    assert response.data["resolved_at"] is not None


@pytest.mark.django_db
def test_add_comment_to_ticket(auth_client, end_user, admin_user):
    client = auth_client(end_user)
    response = client.post(
        reverse("ticket-list"),
        {
            "title": "Need help with login",
            "description": "Application crashes on login for the user",
            "priority": "LOW",
        },
    )
    ticket_id = response.data["id"]

    admin_client = auth_client(admin_user)
    response = admin_client.post(
        reverse("ticket-comments", args=[ticket_id]),
        {"body": "Looking into this now."},
    )
    assert response.status_code == status.HTTP_201_CREATED

    response = client.get(reverse("ticket-comments", args=[ticket_id]))
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1
    assert response.data[0]["body"] == "Looking into this now."
