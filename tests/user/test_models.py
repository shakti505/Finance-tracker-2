import pytest
from user.models import CustomUser

@pytest.mark.django_db
def test_create_user():
    """Test creating a user with create_user()"""
    user = CustomUser.objects.create_user(
        name="Test User",
        email="test@example.com",
        username="testuser",
        password="SecurePass123"
    )
    assert user.email == "test@example.com"
    assert user.username == "testuser"
    assert user.check_password("SecurePass123")
@pytest.mark.django_db
def test_create_superuser():
    """Test creating a superuser"""
    admin_user = CustomUser.objects.create_superuser(
        name="Admin User",
        email="admin@example.com",
        username="admin",
        password="AdminPass123"
    )
    assert admin_user.is_superuser is True
    assert admin_user.is_staff is True

@pytest.mark.django_db
def test_user_str():
    """Test the string representation of the user model"""
    user = CustomUser.objects.create_user(
        email="test@example.com", username="testuser", password="password123"
    )
    assert str(user) == "test@example.com"  # ✅ Should return email in __str__()
