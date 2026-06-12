"""
seed_demo_data.py

Creates a small set of demo users and tickets so the API is immediately
useful to explore after a fresh `migrate` -- useful for local
exploration, screenshots, and demos.

Usage:
    python manage.py seed_demo_data
"""

from django.core.management.base import BaseCommand

from tickets.models import Ticket
from users.models import User


DEMO_USERS = [
    {
        "username": "admin", "password": "adminpass123",
        "role": User.Role.ADMIN, "is_staff": True, "is_superuser": True,
    },
    {
        "username": "net_engineer", "password": "engineerpass123",
        "role": User.Role.ENGINEER, "team": "NETWORK",
    },
    {
        "username": "db_engineer", "password": "engineerpass123",
        "role": User.Role.ENGINEER, "team": "DATABASE",
    },
    {
        "username": "cloud_engineer", "password": "engineerpass123",
        "role": User.Role.ENGINEER, "team": "CLOUD",
    },
    {"username": "alice", "password": "userpass123", "role": User.Role.USER},
    {"username": "bob", "password": "userpass123", "role": User.Role.USER},
]

DEMO_TICKETS = [
    {
        "title": "Cannot connect to office VPN",
        "description": "VPN connection failing for remote employee since this morning.",
        "priority": Ticket.Priority.HIGH,
        "username": "alice",
    },
    {
        "title": "Production database is extremely slow",
        "description": (
            "Queries on the orders database are running extremely slow "
            "today and CPU usage is high."
        ),
        "priority": Ticket.Priority.CRITICAL,
        "username": "bob",
    },
    {
        "title": "EC2 instance unresponsive",
        "description": "The web-prod-01 EC2 instance is not responding to health checks.",
        "priority": Ticket.Priority.HIGH,
        "username": "alice",
    },
    {
        "title": "App crashes on login",
        "description": "The customer portal application crashes on login for the user.",
        "priority": Ticket.Priority.MEDIUM,
        "username": "bob",
    },
    {
        "title": "CI pipeline failing",
        "description": "GitHub Actions pipeline for billing-service is failing at the build step.",
        "priority": Ticket.Priority.LOW,
        "username": "alice",
    },
]


class Command(BaseCommand):
    help = "Seed the database with demo users and tickets."

    def handle(self, *args, **options):
        created_users = {}

        for spec in DEMO_USERS:
            spec = dict(spec)
            username = spec.pop("username")
            password = spec.pop("password")
            user, created = User.objects.get_or_create(username=username, defaults=spec)
            if created:
                user.set_password(password)
                user.save()
                self.stdout.write(self.style.SUCCESS(f"Created user '{username}'"))
            else:
                self.stdout.write(f"User '{username}' already exists, skipping")
            created_users[username] = user

        for spec in DEMO_TICKETS:
            spec = dict(spec)
            username = spec.pop("username")
            if Ticket.objects.filter(title=spec["title"]).exists():
                self.stdout.write(f"Ticket '{spec['title']}' already exists, skipping")
                continue

            ticket = Ticket.objects.create(created_by=created_users[username], **spec)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Created ticket '{ticket.title}' "
                    f"-> routed to {ticket.assigned_team} "
                    f"(confidence={ticket.routed_confidence})"
                )
            )

        self.stdout.write(self.style.SUCCESS("\nDemo data ready. Sample logins:"))
        for spec in DEMO_USERS:
            self.stdout.write(f"  {spec['username']} / {spec.get('password', '')}")
