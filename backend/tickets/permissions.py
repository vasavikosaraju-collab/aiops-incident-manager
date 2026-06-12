from rest_framework import permissions


class IsOwnerOrEngineer(permissions.BasePermission):
    """Object-level permission for tickets.

    - Read access: the ticket's creator, OR any ENGINEER/ADMIN.
    - Write access (update/delete): only ENGINEER/ADMIN users. Regular
      users can create tickets and comment, but cannot change status,
      priority, or assignment themselves once a ticket exists -- that
      models a real support workflow where the requester opens a ticket
      and engineers manage its lifecycle.
    """

    def has_object_permission(self, request, view, obj):
        user = request.user

        if request.method in permissions.SAFE_METHODS:
            return user.is_engineer or obj.created_by_id == user.id

        return user.is_engineer


class IsEngineer(permissions.BasePermission):
    """Used for endpoints (like /api/predict-team/) that should only be
    callable by support staff, not end users."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_engineer)
