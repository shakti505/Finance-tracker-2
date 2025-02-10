
from rest_framework import permissions

class IsStaffOrOwner(permissions.BasePermission):
    """
    Custom permission to:
    - Allow staff users to access and modify all objects.
    - Allow normal users to access objects based on certain conditions.
    """

    def has_object_permission(self, request, view, obj):
        # GET requests: Allow based on the existing logic
        if request.method == "GET":
            if request.user.is_staff:
                return True  # Staff can access all categories
            return not obj.is_deleted or (obj.is_predefined and obj.user == request.user)

        #  PATCH & DELETE: Staff can modify any object except is_deleted = True
        if request.user.is_staff:
            return not obj.is_deleted

        # Normal users: Can only modify their own objects, and only if not soft-deleted
        return not obj.is_deleted and obj.user == request.user
