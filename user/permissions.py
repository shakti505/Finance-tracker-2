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


# # serializers.py
# class UpdatePasswordSerializer(serializers.Serializer):
#     current_password = serializers.CharField(write_only=True, required=False)
#     new_password = serializers.CharField(write_only=True)
#     confirm_password = serializers.CharField(write_only=True)

#     def validate(self, data):
#         user = self.context["user"]
#         request_user = self.context["request"].user

#         # Staff can update password without current password
#         if not request_user.is_staff:
#             if "current_password" not in data:
#                 raise ValidationError("Current password is required.")
#             if not user.check_password(data["current_password"]):
#                 raise ValidationError("Current password is incorrect.")

#         # Validate new passwords
#         if data["new_password"] != data["confirm_password"]:
#             raise ValidationError("New passwords do not match.")

#         try:
#             validate_password(data["new_password"], user)
#         except ValidationError as e:
#             raise ValidationError({"new_password": list(e.messages)})

#         # Prevent reusing current password for non-staff users
#         if not request_user.is_staff and user.check_password(data["new_password"]):
#             raise ValidationError("New password cannot be the same as the current password.")

#         return data

#     def update_password(self):
#         try:
#             user = self.context["user"]
#             user.set_password(self.validated_data["new_password"])
#             user.save()

#             # Invalidate all other tokens except current one only for non-staff users
#             if not self.context["request"].user.is_staff:
#                 ActiveTokens.objects.filter(user=user).exclude(
#                     token=self.context["request"].auth
#                 ).delete()

#             logger.info(f"Password updated successfully for user {user.username}")
#             return True
#         except Exception as e:
#             logger.error(f"Error updating password for user {user.username}: {str(e)}")
#             raise serializers.ValidationError("Error updating password. Please try again.")


# class DeleteUserSerializer(serializers.Serializer):
#     password = serializers.CharField(write_only=True, required=False)

#     def validate(self, data):
#         user = self.context["user"]
#         request_user = self.context["request"].user

#         # Only require password for non-staff users
#         if not request_user.is_staff:
#             if "password" not in data:
#                 raise ValidationError("Password is required.")
#             if not user.check_password(data["password"]):
#                 raise ValidationError("Incorrect password")

#         return data

#     def delete_user(self):
#         try:
#             user = self.context["user"]

#             # Soft delete user
#             user.is_active = False
#             user.save()

#             # Update related records if user is staff
#             if user.is_staff:
#                 Category.objects.filter(user=user).update(user=None)

#             # Invalidate all tokens
#             ActiveTokens.objects.filter(user=user).delete()

#             logger.info(f"User {user.username} soft-deleted successfully.")
#             return True
#         except Exception as e:
#             logger.error(f"Error deleting user {user.username}: {str(e)}")
#             raise serializers.ValidationError("Error deleting user. Please try again.")


# class UpdateUserSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = CustomUser
#         fields = ["username", "email", "name"]

#     def validate(self, data):
#         request_user = self.context["request"].user
#         user = self.context["user"]

#         # Staff can update any user's details
#         if request_user.is_staff:
#             return data

#         # For non-staff users, ensure they're only updating their own data
#         if user.id != request_user.id:
#             raise PermissionDenied("You don't have permission to update this user's details.")

#         return data

#     def validate_username(self, value):
#         try:
#             user = self.context["user"]
#             if CustomUser.objects.exclude(pk=user.pk).filter(username=value).exists():
#                 raise ValidationError("Username already exists")
#             return value
#         except Exception as e:
#             logger.error(f"Error validating username: {str(e)}")
#             raise ValidationError("Error validating username")

#     def validate_email(self, value):
#         try:
#             user = self.context["user"]
#             if CustomUser.objects.exclude(pk=user.pk).filter(email=value).exists():
#                 raise ValidationError("Email already exists")
#             return value
#         except Exception as e:
#             logger.error(f"Error validating email: {str(e)}")
#             raise ValidationError("Error validating email")


# # views.py
# class UserProfileView(BaseUserView, TokenAuthorizationMixin, APIView):
#     permission_classes = [IsStaffOrOwner]

#     def get(self, request, id):
#         try:
#             user = self.get_user_or_404(id)
#             self.check_object_permissions(request, user)
#             serializer = UserSerializer(user)
#             return success_single_response(serializer.data)
#         except Exception as e:
#             logger.error(f"Error retrieving user profile: {str(e)}")
#             return validation_error_response("Error retrieving user profile")

#     def patch(self, request, id):
#         try:
#             user = self.get_user_or_404(id)
#             self.check_object_permissions(request, user)
#             serializer = UpdateUserSerializer(
#                 instance=user,
#                 data=request.data,
#                 context={"request": request, "user": user},
#                 partial=True
#             )
#             if not serializer.is_valid():
#                 return validation_error_response(serializer.errors)
#             serializer.save()
#             return success_single_response(serializer.data)
#         except Exception as e:
#             logger.error(f"Error updating user profile: {str(e)}")
#             return validation_error_response("Error updating user profile")

#     def delete(self, request, id):
#         try:
#             user = self.get_user_or_404(id)
#             self.check_object_permissions(request, user)

#             serializer = DeleteUserSerializer(
#                 data=request.data,
#                 context={"request": request, "user": user}
#             )

#             if not serializer.is_valid():
#                 return validation_error_response(serializer.errors)

#             serializer.delete_user()
#             return success_response(
#                 {"message": "User account deleted"},
#                 status_code=status.HTTP_200_OK
#             )
#         except Exception as e:
#             logger.error(f"Error deleting user: {str(e)}")
#             return validation_error_response("Error deleting user")


# class UpdatePasswordView(BaseUserView, APIView):
#     permission_classes = [IsStaffOrOwner]

#     def patch(self, request, id):
#         try:
#             user = self.get_user_or_404(id)
#             if isinstance(user, Response):
#                 return user

#             self.check_object_permissions(request, user)

#             serializer = UpdatePasswordSerializer(
#                 data=request.data,
#                 context={"request": request, "user": user}
#             )

#             if not serializer.is_valid():
#                 return validation_error_response(serializer.errors)

#             serializer.update_password()
#             return success_response({"message": "Password updated successfully"})
#         except Exception as e:
#             logger.error(f"Error updating password: {str(e)}")
#             return validation_error_response("Error updating password")
