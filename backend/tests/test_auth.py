import pytest
from django.urls import reverse
from rest_framework import status

from users.models import User


@pytest.mark.django_db
def test_register_and_login(api_client):
    register_url = reverse("register")
    payload = {
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "StrongPass123!",
    }

    response = api_client.post(register_url, payload)
    assert response.status_code == status.HTTP_201_CREATED
    assert User.objects.filter(username="newuser").exists()
    # Password must never be echoed back.
    assert "password" not in response.data

    token_url = reverse("token_obtain_pair")
    response = api_client.post(
        token_url, {"username": "newuser", "password": "StrongPass123!"}
    )
    assert response.status_code == status.HTTP_200_OK
    assert "access" in response.data
    assert "refresh" in response.data


@pytest.mark.django_db
def test_me_endpoint_requires_authentication(api_client):
    response = api_client.get(reverse("me"))
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_me_endpoint_returns_current_user(auth_client, end_user):
    client = auth_client(end_user)
    response = client.get(reverse("me"))

    assert response.status_code == status.HTTP_200_OK
    assert response.data["username"] == "alice"
    assert response.data["role"] == "USER"
