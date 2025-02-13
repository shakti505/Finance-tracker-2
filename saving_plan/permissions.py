from rest_framework import permissions


# class IsSavingsPlanUser(permissions.BasePermission):

#     def has_object_permission(self, request, view, obj):
#         if request.user.is_staff:
#             return True

#         if hasattr(obj, "user"):
#             return obj.user == request.user
#         elif hasattr(obj, "savings_plan"):
#             return obj.savings_plan.user == request.user
#         return False


class IsSavingsPlanUser(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object or staff to access it.
    """

    def has_object_permission(self, request, view, obj):
        # Ensure the user is authenticated

        # Staff has full access
        if request.user.is_staff:
            return not obj.is_deleted

        # Owners have access only if the object is not deleted
        return not obj.is_deleted and obj.user == request.user
