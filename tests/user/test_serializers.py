# import pytest
# from user.serializers import UserSerializer, LoginSerializer
# from user.models import CustomUser
# from rest_framework.test import APIRequestFactory
# import uuid

# @pytest.mark.parametrize("name,username,email,password",[
#         ("test","username","testuser@emaul.com", "password12345"),
#     ],)
# @pytest.mark.django_db
# def test_user_serializer(name,username,email,password, create_user):
#     """Test user serializer with valid data"""
#     user = create_user(name=name,username=username,email=email, password=password)
#     serializer = UserSerializer(user)
#     assert serializer.data["name"] == name
#     assert serializer.data["email"] == email
#     assert serializer.data["username"] == username

# @pytest.mark.django_db
# def test_user_serializer_invalid():
#     """Test user serializer with missing required fields"""
#     invalid_data = {"email": "invalid@example.com"}  
#     serializer = UserSerializer(data=invalid_data)

#     assert not serializer.is_valid()
#     assert "username" in serializer.errors
#     assert "password" in serializer.errors

# @pytest.mark.django_db
# def test_user_login(create_user):
#     """Test user login serializer"""
#     user = create_user(email="test@email.com",username="testuser", password="password123")
#     serializer = LoginSerializer(data={"username": "testuser", "password": "password123"})
#     assert serializer.is_valid()
#     assert "user" in serializer.validated_data
import pytest
from user.serializers import (
    UserSerializer, LoginSerializer, UpdatePasswordSerializer,
    DeleteUserSerializer, UpdateUserSerializer, PasswordResetRequestSerializer
)
from user.models import CustomUser
from django.contrib.auth import get_user_model, authenticate
from rest_framework.test import APIRequestFactory
from rest_framework.exceptions import ValidationError, AuthenticationFailed
from unittest.mock import patch

User = get_user_model()


@pytest.mark.django_db
def test_user_creation_password_hashing():
    """Ensure password is hashed when creating a user"""
    data = {
        "name": "Test User",
        "username": "testuser",
        "email": "test@example.com",
        "password": "StrongPass123!"
    }
    serializer = UserSerializer(data=data)
    assert serializer.is_valid(), serializer.errors

    user = serializer.save()
    assert user.check_password("StrongPass123!")  # Password should be hashed


@pytest.mark.django_db
def test_login_serializer_valid(create_user):
    """Test LoginSerializer with valid credentials"""
    create_user(username="testuser", email="test@example.com", password="password123")
    serializer = LoginSerializer(data={"username": "testuser", "password": "password123"})
    
    assert serializer.is_valid()
    assert "user" in serializer.validated_data


@pytest.mark.django_db
def test_login_serializer_invalid(mocker):
    """Test LoginSerializer with invalid credentials"""
    mocker.patch("django.contrib.auth.authenticate", return_value=None)
    serializer = LoginSerializer(data={"username": "wronguser", "password": "wrongpass"})
    assert not serializer.is_valid()
    assert "non_field_errors" in serializer.errors


@pytest.mark.django_db
def test_login_serializer_inactive_user(create_user):
    """Test LoginSerializer rejects inactive users"""
    user = create_user(username="testuser", email="test@example.com", password="password123")
    user.is_active = False
    user.save()
    
    serializer = LoginSerializer(data={"username": "testuser", "password": "password123"})
    
    with pytest.raises(AuthenticationFailed, match="Account is inactive"):
        serializer.is_valid(raise_exception=True)


@pytest.mark.django_db
def test_update_password_serializer_valid(create_user):
    """Test UpdatePasswordSerializer with valid password change"""
    user = create_user(username="testuser", email="test@example.com", password="oldpassword")

    request = APIRequestFactory().post("/")
    request.user = user
    request.auth = "dummy_token"  # Ensure auth is available

    serializer = UpdatePasswordSerializer(
        data={
            "current_password": "oldpassword",
            "new_password": "newsecurepassword",
            "confirm_password": "newsecurepassword"
        },
        context={"user": user, "request": request}
    )

    assert serializer.is_valid(), serializer.errors

    serializer.update_password()
    user.refresh_from_db()
    assert user.check_password("newsecurepassword")


@pytest.mark.django_db
def test_delete_user_serializer_valid(create_user):
    """Test DeleteUserSerializer with valid password"""
    user = create_user(username="testuser", email="test@example.com", password="password123")

    request = APIRequestFactory().delete("/")
    request.user = user

    serializer = DeleteUserSerializer(
        data={"password": "password123"},
        context={"user": user, "request": request}
    )

    assert serializer.is_valid()
    assert serializer.delete_user()
    user.refresh_from_db()
    assert not user.is_active  # Should be soft deleted


@pytest.mark.django_db
def test_delete_user_serializer_invalid_password(create_user):
    """Test DeleteUserSerializer with incorrect password"""
    user = create_user(username="testuser", email="test@example.com", password="password123")

    request = APIRequestFactory().delete("/")
    request.user = user

    serializer = DeleteUserSerializer(
        data={"password": "wrongpassword"},
        context={"user": user, "request": request}
    )

    assert not serializer.is_valid()
    assert "non_field_errors" in serializer.errors  # Error should be under non_field_errors


@pytest.mark.django_db
def test_update_user_serializer_valid(create_user):
    """Test UpdateUserSerializer with valid update"""
    user = create_user(username="testuser", email="test@example.com", password="password123")

    request = APIRequestFactory().patch("/")
    request.user = user

    serializer = UpdateUserSerializer(
        instance=user,
        data={"username": "updateduser", "email": "updated@example.com"},
        context={"user": user, "request": request}
    )

    assert serializer.is_valid(), serializer.errors
    serializer.save()
    user.refresh_from_db()
    assert user.username == "updateduser"
    assert user.email == "updated@example.com"


@pytest.mark.django_db
def test_update_user_serializer_invalid_email(create_user):
    """Test UpdateUserSerializer rejects duplicate email"""
    create_user(username="existinguser", email="existing@example.com", password="password123")
    user = create_user(username="testuser", email="test@example.com", password="password123")

    request = APIRequestFactory().patch("/")
    request.user = user

    serializer = UpdateUserSerializer(
        instance=user,
        data={"email": "existing@example.com"},
        context={"user": user, "request": request}
    )

    assert not serializer.is_valid()
    assert "email" in serializer.errors


@pytest.mark.django_db
def test_password_reset_request_serializer(create_user):
    """Test PasswordResetRequestSerializer with valid email"""
    create_user(username="testuser", email="test@example.com", password="password123")

    serializer = PasswordResetRequestSerializer(data={"email": "test@example.com"})
    assert serializer.is_valid()


@pytest.mark.django_db
def test_password_reset_request_serializer_invalid():
    """Test PasswordResetRequestSerializer with unknown email"""
    serializer = PasswordResetRequestSerializer(data={"email": "unknown@example.com"})

    assert not serializer.is_valid()
    assert "email" in serializer.errors
