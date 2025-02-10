from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from rest_framework.response import Response
from .permissions import IsStaffUser, IsStaffOrOwner
from utils.responses import (
    success_response,
    validation_error_response,
    success_single_response,
    not_found_error_response,
    success_no_content_response,
)
from uuid import UUID
from utils.token import TokenHandler
from .models import CustomUser
from .serializers import (
    UserSerializer,
    LoginSerializer,
    UpdatePasswordSerializer,
    DeleteUserSerializer,
    UpdateUserSerializer,
)
from .swagger_docs import (
    user_create_doc,
    login_doc,
    logout_doc,
    user_profile_get_doc,
    user_profile_patch_doc,
    user_profile_delete_doc,
    password_reset_request_doc,
)
from .tasks import send_email_task as send_mail
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from .serializers import PasswordResetRequestSerializer
from django.utils.http import urlsafe_base64_decode
from utils.logging import logger


class BaseUserView:
    """
    Base class for common user-related view operations
    """

    def get_user_or_404(self, id):
        """
        Retrieve user by ID or raise NotFound exception
        """
        try:
            user = CustomUser.objects.get(id=id)
            return user
        except CustomUser.DoesNotExist:
            return not_found_error_response(f"No user found with ID: {id}")


class UserCreateView(APIView):
    permission_classes = [AllowAny]

    @user_create_doc
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return success_single_response(serializer.data)
        return validation_error_response(serializer.errors)


class LoginView(APIView):
    permission_classes = [AllowAny]

    @login_doc
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data["user"]
            tokens = TokenHandler.generate_tokens_for_user(user)
            return success_response(tokens)
        return validation_error_response(serializer.errors)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @logout_doc
    def post(self, request):
        TokenHandler.invalidate_user_session(request.user, request.auth)
        return success_single_response({"message": "Logged out successfully"})


class UserListView(APIView):
    permission_classes = [IsStaffUser, IsAuthenticated]

    @user_profile_get_doc
    def get(self, request):
        users = CustomUser.objects.all()
        serializer = UserSerializer(users, many=True)
        return success_response(serializer.data)


class UserProfileView(BaseUserView, APIView):
    permission_classes = [IsStaffOrOwner, IsAuthenticated]

    @user_profile_get_doc
    def get(self, request, id):
        try:
            user = self.get_user_or_404(id)
            self.check_object_permissions(request, user)
            serializer = UserSerializer(user)
            return success_single_response(serializer.data)
        except Exception as e:
            return not_found_error_response()

    @user_profile_patch_doc
    def patch(self, request, id):
        try:
            user = self.get_user_or_404(id)
            self.check_object_permissions(request, user)
            serializer = UpdateUserSerializer(
                instance=user,
                data=request.data,
                context={"request": request, "user": user},
                partial=True,
            )
            if serializer.is_valid():
                serializer.save()
                return success_single_response(serializer.data)
            return validation_error_response(serializer.errors)
        except Exception as e:
            logger.error(f"Error updating user profile: {str(e)}")
            return not_found_error_response()

    @user_profile_delete_doc
    def delete(self, request, id):
        try:
            user = self.get_user_or_404(id)
            self.check_object_permissions(request, user)

            serializer = DeleteUserSerializer(
                data=request.data, context={"request": request, "user": user}
            )
            if serializer.is_valid():
                serializer.delete_user()
                return success_no_content_response()
            return validation_error_response(serializer.errors)
        except Exception as e:
            logger.error(f"Error deleting user: {str(e)}")
            return not_found_error_response("Error deleting user")


class UpdatePasswordView(BaseUserView, APIView):
    permission_classes = [IsStaffOrOwner, IsAuthenticated]

    @password_reset_request_doc
    def patch(self, request, id):
        try:
            user = self.get_user_or_404(id)
            if isinstance(user, Response):
                return user

            self.check_object_permissions(request, user)

            serializer = UpdatePasswordSerializer(
                data=request.data, context={"request": request, "user": user}
            )

            if serializer.is_valid():
                serializer.update_password()
                return success_response("Successfully updated password.")
            return validation_error_response(serializer.errors)
        except Exception as e:
            logger.error(f"Error updating password: {str(e)}")
            return not_found_error_response(f"{e}")


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    @password_reset_request_doc
    def post(self, request):
        # Use your custom serializer
        serializer = PasswordResetRequestSerializer(data=request.data)

        if serializer.is_valid():
            email = serializer.validated_data["email"]
            try:
                user = CustomUser.objects.get(email=email)
            except CustomUser.DoesNotExist:
                return not_found_error_response(
                    detail="User with this email not found."
                )

            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(
                str(user.pk).encode()
            )  # Use UUID bytes for encoding

            # Generate reset URL
            reset_link = (
                f"http://localhost:8000/api/auth/password-reset/confirm/{uid}/{token}/"
            )

            # Send email
            send_mail.delay(
                [email],
                reset_link,
            )
            return success_response(data={"message": "Password reset email sent."})

        return validation_error_response(serializer.errors)


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, uidb64, token):
        try:
            # Decode UID
            uid = urlsafe_base64_decode(uidb64).decode()

            # Ensure the UID is a valid UUID
            uid = UUID(uid)  # This will raise a ValueError if the UID is invalid

            # Fetch the user using the decoded UID
            user = CustomUser.objects.get(id=uid)
        except (ValueError, CustomUser.DoesNotExist, TypeError):
            return not_found_error_response(detail="Invalid user or token.")

        if default_token_generator.check_token(user, token):
            new_password = request.data.get("password")
            if new_password:
                user.set_password(new_password)
                user.save()
                return success_response(
                    data={"message": "Password has been reset successfully."}
                )
            return validation_error_response(errors={"detail": "Password is required."})

        return validation_error_response(errors={"detail": "Invalid or expired token."})
