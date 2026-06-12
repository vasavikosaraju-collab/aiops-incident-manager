import pytest
from rest_framework.test import APIClient

from users.models import User


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def end_user(db):
    return User.objects.create_user(
        username="alice", password="testpass123", role=User.Role.USER
    )


@pytest.fixture
def network_engineer(db):
    return User.objects.create_user(
        username="bob",
        password="testpass123",
        role=User.Role.ENGINEER,
        team="NETWORK",
    )


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        username="admin",
        password="testpass123",
        role=User.Role.ADMIN,
    )


@pytest.fixture
def auth_client():
    """Returns a helper that logs in a given user with a *fresh*
    APIClient instance and returns it (JWT/force-auth based)."""

    def _auth(user):
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    return _auth
