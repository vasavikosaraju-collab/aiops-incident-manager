from django.contrib import admin

from .models import Ticket, TicketComment


class TicketCommentInline(admin.TabularInline):
    model = TicketComment
    extra = 0
    readonly_fields = ("author", "created_at")


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "priority",
        "status",
        "assigned_team",
        "routed_confidence",
        "created_by",
        "created_at",
        "is_overdue",
    )
    list_filter = ("priority", "status", "assigned_team")
    search_fields = ("title", "description")
    inlines = [TicketCommentInline]
