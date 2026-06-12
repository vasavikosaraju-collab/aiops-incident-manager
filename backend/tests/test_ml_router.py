import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
def test_predict_team_requires_authentication(api_client):
    response = api_client.post(
        reverse("predict-team"), {"description": "VPN connection failing"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
@pytest.mark.parametrize(
    "description,expected_team",
    [
        ("VPN connection failing for remote employee", "NETWORK"),
        ("Database queries are timing out and CPU usage is high", "DATABASE"),
        ("AWS EC2 instance is not responding to health checks", "CLOUD"),
    ],
)
def test_predict_team_returns_expected_category(
    auth_client, end_user, description, expected_team
):
    client = auth_client(end_user)
    response = client.post(reverse("predict-team"), {"description": description})

    assert response.status_code == status.HTTP_200_OK
    assert response.data["team"] == expected_team
    assert 0 <= response.data["confidence"] <= 1


@pytest.mark.django_db
def test_predict_team_requires_description(auth_client, end_user):
    client = auth_client(end_user)
    response = client.post(reverse("predict-team"), {})
    assert response.status_code == status.HTTP_400_BAD_REQUEST
