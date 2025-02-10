from rest_framework import permissions


class IsSavingsPlanUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True

        if hasattr(obj, "user"):
            return obj.user == request.user
        elif hasattr(obj, "savings_plan"):
            return obj.savings_plan.user == request.user
        return False
