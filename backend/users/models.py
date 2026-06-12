"""
Custom user model.

We extend Django's AbstractUser instead of using the default User so we
can attach a `role` field. Roles drive permission checks throughout the
`tickets` app (e.g. only ENGINEER/ADMIN users can change a ticket's
status or assigned team).
"""

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):

    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        ENGINEER = "ENGINEER", "Support Engineer"
        USER = "USER", "End User"

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.USER,
        help_text="Determines what the user can do via the API.",
    )

    team = models.CharField(
        max_length=30,
        blank=True,
        help_text="Support team this user belongs to (engineers only), "
        "e.g. NETWORK, DATABASE, SECURITY, CLOUD, APPLICATION, DEVOPS.",
    )

    def __str__(self):
        return f"{self.username} ({self.role})"

    @property
    def is_engineer(self):
        return self.role in (self.Role.ENGINEER, self.Role.ADMIN)
