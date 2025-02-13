from rest_framework.permissions import BasePermission


class IsStaffOrOwner(BasePermission):
    """
    Custom permission to only allow owners of an object or staff to access it.
    """

    def has_object_permission(self, request, view, obj):
        # Staff permissions
        if request.method == "GET":
            if request.user.is_staff:
                return True

        if request.user.is_staff:
            return not obj.is_deleted

        return not obj.is_deleted and obj.user == request.user
