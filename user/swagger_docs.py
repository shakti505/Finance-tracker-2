from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from .serializers import (
    UserSerializer,
    LoginSerializer,
    UpdatePasswordSerializer,
    DeleteUserSerializer,
    UpdateUserSerializer,
    PasswordResetRequestSerializer,
)

# 📌 Swagger Documentation for User Registration
user_create_doc = swagger_auto_schema(
    operation_summary="Create a new user",
    operation_description="Registers a new user and returns their details.",
    request_body=UserSerializer,
    responses={
        201: UserSerializer,
        400: openapi.Response("Validation error"),
    },
)

# 📌 Swagger Documentation for User Login
login_doc = swagger_auto_schema(
    operation_summary="User Login",
    operation_description="Logs in a user and returns authentication tokens.",
    request_body=LoginSerializer,
    responses={
        200: openapi.Response("JWT Token Response"),
        400: openapi.Response("Invalid credentials"),
    },
)

# 📌 Swagger Documentation for Logging Out
logout_doc = swagger_auto_schema(
    operation_summary="User Logout",
    operation_description="Logs out a user by invalidating their token.",
    responses={
        200: openapi.Response("Logged out successfully"),
        401: openapi.Response("Authentication required"),
    },
)

# 📌 Swagger Documentation for Getting User Profile
user_profile_get_doc = swagger_auto_schema(
    operation_summary="Get User Profile",
    operation_description="Retrieve user details by ID.",
    responses={
        200: UserSerializer,
        404: openapi.Response("User not found"),
    },
)

# 📌 Swagger Documentation for Updating User Profile
user_profile_patch_doc = swagger_auto_schema(
    operation_summary="Update User Profile",
    operation_description="Update specific fields of a user profile. Only staff or the user themselves can update it.",
    request_body=UpdateUserSerializer,
    responses={
        200: UserSerializer,
        400: openapi.Response("Validation error"),
        404: openapi.Response("User not found"),
    },
)

# 📌 Swagger Documentation for Deleting User
user_profile_delete_doc = swagger_auto_schema(
    operation_summary="Delete User",
    operation_description="Delete a user account. Requires proper permissions.",
    request_body=DeleteUserSerializer,
    responses={
        204: openapi.Response("User deleted successfully"),
        400: openapi.Response("Validation error"),
        404: openapi.Response("User not found"),
    },
)

# 📌 Swagger Documentation for Password Reset Request
password_reset_request_doc = swagger_auto_schema(
    operation_summary="Request Password Reset",
    operation_description="Sends a password reset email to the provided email address.",
    request_body=PasswordResetRequestSerializer,
    responses={
        200: openapi.Response("Password reset email sent."),
        400: openapi.Response("Validation error"),
        404: openapi.Response("User not found"),
    },
)
