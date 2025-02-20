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
import os
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
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .tasks import soft_delete_related_data
from rest_framework.exceptions import NotFound


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
            raise NotFound(detail="User not found.")


class UserCreateView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @user_create_doc
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return success_single_response(serializer.data, status_code=status.HTTP_201_CREATED)
        return validation_error_response(serializer.errors)


class LoginView(APIView):
    authentication_classes = []
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
        return success_single_response({"detail": "Logged out successfully"})


class UserListView(APIView):
    permission_classes = [ IsAuthenticated, IsStaffUser]    

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
        except Exception:
            return not_found_error_response(f"No user found with ID: {id}")
        serializer = UserSerializer(user)
        return success_single_response(serializer.data)

    @user_profile_patch_doc
    def patch(self, request, id):
        try:
            user = self.get_user_or_404(id)
            self.check_object_permissions(request, user)
        except Exception:
            return not_found_error_response(f"No user found with ID: {id}")
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

    @user_profile_delete_doc
    def delete(self, request, id):
        try:
            user = self.get_user_or_404(id)
            self.check_object_permissions(request, user)
        except Exception:
            return not_found_error_response(f"No user found with ID: {id}")
        serializer = DeleteUserSerializer(
            data=request.data, context={"request": request, "user": user}
        )
        if serializer.is_valid():
            serializer.delete_user()
            soft_delete_related_data.delay(user.id)
            return success_no_content_response()
        return validation_error_response(serializer.errors)


class UpdatePasswordView(BaseUserView, APIView):
    permission_classes = [IsStaffOrOwner, IsAuthenticated]

    @password_reset_request_doc
    def patch(self, request, id):
        try:
            user = self.get_user_or_404(id)
            self.check_object_permissions(request, user)
        except Exception:
            return not_found_error_response(f"No user found with ID: {id}")
        serializer = UpdatePasswordSerializer(
            data=request.data, context={"request": request, "user": user}
        )

        if serializer.is_valid():
            serializer.update_password()
            return success_response({"detail": "Successfully updated password."})
        return validation_error_response(serializer.errors)


class PasswordResetRequestView(APIView):
    authentication_classes = []
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
            uid = urlsafe_base64_encode(str(user.id).encode())


            reset_link = f"http://localhost:8000/api/v1/auth/password-reset/confirm/{uid}/{token}/"
            print(reset_link)

            send_mail.delay(
                [email],
                reset_link,
            )
            return success_response(data={"message": "Password reset email sent."})

        return validation_error_response(serializer.errors)


class PasswordResetConfirmView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request, uidb64, token):
        try:
            # Decode UID and fetch user
            uid = UUID(urlsafe_base64_decode(uidb64).decode())
            user = CustomUser.objects.get(id=uid)

            # Validate token
            if not default_token_generator.check_token(user, token):
                return validation_error_response(
                    {"detail": "Invalid or expired token."}
                )

            # Validate and set new password
            new_password = request.data.get("password")
            if not new_password:
                return validation_error_response({"detail": "Password is required."})

            validate_password(new_password, user)  # Ensure strong password
            user.set_password(new_password)
            user.save()
            return success_response(
                {"message": "Password has been reset successfully."}
            )

        except (ValueError, TypeError, CustomUser.DoesNotExist):
            return not_found_error_response("Invalid user or token.")
