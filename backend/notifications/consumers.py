from channels.generic.websocket import AsyncJsonWebsocketConsumer


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    """WebSocket consumer for real-time incident alerts.

    Connect to:  ws://<host>/ws/notifications/

    On connect, the authenticated user is added to two channel groups:
      - "user_<id>"  - direct notifications addressed to this user
      - "team_<team>" - broadcast alerts for the user's support team
                        (only joined if the user has a `team` set, i.e.
                        they are an engineer)

    Messages are pushed by `tickets.signals` via
    `channel_layer.group_send(...)` whenever a CRITICAL ticket is
    created. The payload looks like:

        {
            "type": "incident_alert",
            "ticket_id": 42,
            "title": "Production database unreachable",
            "priority": "CRITICAL",
            "assigned_team": "DATABASE",
            "message": "New CRITICAL ticket routed to DATABASE: ..."
        }
    """

    async def connect(self):
        user = self.scope["user"]

        if not user or not user.is_authenticated:
            await self.close()
            return

        self.groups_joined = [f"user_{user.id}"]

        team = getattr(user, "team", "") or ""
        if team:
            self.groups_joined.append(f"team_{team}")

        for group in self.groups_joined:
            await self.channel_layer.group_add(group, self.channel_name)

        await self.accept()

    async def disconnect(self, code):
        for group in getattr(self, "groups_joined", []):
            await self.channel_layer.group_discard(group, self.channel_name)

    # Handler name must match the "type" key (with dots replaced by
    # underscores) sent via group_send, i.e. "incident.alert" ->
    # incident_alert.
    async def incident_alert(self, event):
        await self.send_json(event)
