from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    """Read-only representation of a user, used by /api/auth/me/ and
    nested inside ticket responses (created_by, assigned_to)."""

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "team",
        ]
        read_only_fields = fields


class RegisterSerializer(serializers.ModelSerializer):
    """Used by POST /api/auth/register/ to create a new account.

    `role` and `team` are accepted so the demo/seed data can create
    engineers belonging to specific teams, but in a real production
    deployment you would typically restrict role assignment to admins
    only (e.g. default every self-registration to USER and have an
    admin endpoint to promote engineers).
    """

    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "password",
            "first_name",
            "last_name",
            "role",
            "team",
        ]

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user
