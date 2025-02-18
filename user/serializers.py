from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework.exceptions import ValidationError, AuthenticationFailed
from .models import CustomUser, ActiveTokens
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import PermissionDenied
from utils.logging import logger


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = (
            "id",
            "username",
            "email",
            "password",
            "name",
            "created_at",
            "updated_at",
            "is_active",
            "is_staff",
        )
        extra_kwargs = {
            "password": {"write_only": True},
            "id": {"read_only": True},
            "created_at": {"read_only": True},
            "updated_at": {"read_only": True},
            "is_active": {"read_only": True},
            "is_staff": {"read_only": True},
        }

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        user = CustomUser.objects.create_user(**validated_data)
        logger.info(f"User {user.username} created successfully.")
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        username = data.get("username")
        password = data.get("password")
        user = authenticate(username=username, password=password)
        if not user:
            raise AuthenticationFailed("Invalid credentials")

        if not user.is_active:
            raise AuthenticationFailed("Account is inactive")

        logger.info(f"User {user.username} logged in successfully.")
        data["user"] = user
        return data


class UpdatePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True, required=False)
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = self.context["user"]
        request_user = self.context["request"].user

        # Staff can update password without current password
        if not request_user.is_superuser:
            if request_user != user:
                raise PermissionDenied("user not found")

            if "current_password" not in data:
                raise ValidationError(
                    {"current_password": "Current password is required."}
                )
            if not user.check_password(data["current_password"]):
                raise ValidationError(
                    {"current_password": "Current password is incorrect."}
                )
            if data["new_password"] == data["current_password"]:
                raise ValidationError(
                    {
                        "new_password": "New password cannot be the same as the current password."
                    }
                )

        if data["new_password"] != data["confirm_password"]:
            raise ValidationError({"confirm_password": "New password do not match."})

        try:
            validate_password(data["new_password"], user)
        except ValidationError as e:
            raise ValidationError({"new_password": list(e.messages)})

        return data

    def update_password(self):
        try:
            user = self.context["user"]
            user.set_password(self.validated_data["new_password"])
            user.save()

            # Invalidate all other tokens except current one only for non-staff users
            if not self.context["request"].user.is_staff:
                ActiveTokens.objects.filter(user=user).exclude(
                    token=self.context["request"].auth
                ).delete()

            logger.info(f"Password updated successfully for user {user.username}")
            return True
        except Exception as e:
            logger.error(f"Error updating password for user {user.username}: {str(e)}")
            raise serializers.ValidationError(
                "Error updating password. Please try again."
            )


class DeleteUserSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True, required=False)

    def validate(self, data):
        user = self.context["user"]
        request_user = self.context["request"].user

        # Only require password for non-staff users
        if not request_user.is_staff:
            if "password" not in data:
                raise ValidationError("Password is required.")
            if not user.check_password(data["password"]):
                raise ValidationError("Incorrect password")

        return data

    def delete_user(self):
        try:
            user = self.context["user"]

            user.is_active = False
            user.save()
            ActiveTokens.objects.filter(user=user).delete()

            logger.info(f"User {user.username} soft-deleted successfully.")
            return True
        except Exception as e:
            logger.error(f"Error deleting user {user.username}: {str(e)}")
            raise serializers.ValidationError("Error deleting user. Please try again.")


class UpdateUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ["username", "email", "name"]

    def validate(self, data):
        request_user = self.context["request"].user
        user = self.context["user"]

        # Staff can update any user's details
        if request_user.is_staff:
            return data

        # For non-staff users, ensure they're only updating their own data
        if user.id != request_user.id:
            raise PermissionDenied(
                "You don't have permission to update this user's details."
            )

        return data

    def validate_username(self, value):
        try:
            user = self.context["user"]
            if CustomUser.objects.exclude(id=user.id).filter(username=value).exists():
                raise ValidationError("Username already exists")
            return value
        except Exception as e:
            logger.error(f"Error validating username: {str(e)}")
            raise ValidationError("Error validating username")

    def validate_email(self, value):
        try:
            user = self.context["user"]
            if CustomUser.objects.exclude(id=user.id).filter(email=value).exists():
                raise ValidationError("Email already exists")
            return value
        except Exception as e:
            logger.error(f"Error validating email: {str(e)}")
            raise ValidationError("Error validating email")


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        try:
            CustomUser.objects.get(email=value, is_active=True)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("No user found with this email address.")
        return value
