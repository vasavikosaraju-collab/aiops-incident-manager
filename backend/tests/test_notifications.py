import pytest
from django.urls import reverse
from rest_framework import status

from notifications.models import Notification


@pytest.mark.django_db
def test_critical_ticket_notifies_team_engineers(
    auth_client, end_user, network_engineer
):
    client = auth_client(end_user)
    response = client.post(
        reverse("ticket-list"),
        {
            "title": "VPN is completely down for everyone",
            "description": "VPN connection failing for remote employee",
            "priority": "CRITICAL",
        },
    )
    assert response.status_code == status.HTTP_201_CREATED

    notification = Notification.objects.get(recipient=network_engineer)
    assert "CRITICAL" in notification.message
    assert notification.is_read is False


@pytest.mark.django_db
def test_non_critical_ticket_does_not_notify(auth_client, end_user, network_engineer):
    client = auth_client(end_user)
    client.post(
        reverse("ticket-list"),
        {
            "title": "Minor VPN hiccup",
            "description": "VPN connection failing for remote employee",
            "priority": "LOW",
        },
    )

    assert not Notification.objects.filter(recipient=network_engineer).exists()


@pytest.mark.django_db
def test_engineer_can_mark_notification_read(
    auth_client, end_user, network_engineer
):
    client = auth_client(end_user)
    client.post(
        reverse("ticket-list"),
        {
            "title": "Critical network outage",
            "description": "VPN connection failing for remote employee",
            "priority": "CRITICAL",
        },
    )

    engineer_client = auth_client(network_engineer)
    list_response = engineer_client.get(reverse("notification-list"))
    assert list_response.status_code == status.HTTP_200_OK
    notification_id = list_response.data["results"][0]["id"]

    response = engineer_client.post(
        reverse("notification-mark-read", args=[notification_id])
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.data["is_read"] is True
