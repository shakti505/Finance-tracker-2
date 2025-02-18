import pytest
from rest_framework.test import APIClient
from django.conf import settings

import pytest
from django.conf import settings

@pytest.fixture(scope="session")
def django_db_setup():
    settings.DATABASES["default"] = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",  # In-memory database
        "ATOMIC_REQUESTS": False,
    }
    print(f"Using database engine: {settings.DATABASES['default']['ENGINE']}")


@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def authenticated_client(db, api_client):
    """Fixture to register, log in, and return an authenticated client"""

    # Register a test user
    register_data = {
        "name": "Test User",
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword"
    }
    register_response = api_client.post('/api/v1//auth/register', register_data)
    assert register_response.status_code == 201, "User registration failed"

    # Log in to get an access token
    login_data = {"username": "testuser", "password": "testpassword"}
    login_response = api_client.post('/api/v1/auth/login', login_data)
    assert login_response.status_code == 200, "User login failed"
    
    # Extract the token correctly
    token = login_response.data.get("data", {}).get("access_token")
    assert token, "Access token not received"
    
    # Set Authorization header for future requests
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    
    return api_client

