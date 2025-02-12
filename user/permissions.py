# permissions.py
from rest_framework.permissions import BasePermission
from rest_framework.exceptions import NotFound


class IsStaffUser(BasePermission):
    """
    Custom permission to only allow staff users.
    """

    def has_permission(self, request, view):
        return request.user.is_staff


class IsStaffOrOwner(BasePermission):
    """
    Custom permission to only allow owners of an object or staff to access it.
    """

    def has_object_permission(self, request, view, obj):
        # Staff can access any user's data
        if request.user.is_staff:
            return True

        # Check if object is active for non-staff users
        if not obj.is_active:
            raise NotFound(detail="Resource not found.")

        # Check if user is accessing their own data
        return obj.id == request.user.id


#         try:
