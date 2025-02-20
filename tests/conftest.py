import pytest
from rest_framework.test import APIClient
from django.db import connection
from user.models import CustomUser
@pytest.fixture
def api_client():
    """Fixture to return a DRF test client"""
    return APIClient()

@pytest.fixture
def authenticated_client(db, api_client):
    """Fixture to register, log in, and return an authenticated client with user ID"""

    # Register a test user
    register_data = {
        "name": "Test User",
        "username": "testuser",
        "email": "test@gmail.com",
        "password": "testpassword"
    }
    register_response = api_client.post('/api/v1/auth/register/', register_data)
    assert register_response.status_code == 201, f"User registration failed: {register_response.data}"

    user_id = register_response.data.get("data", {}).get("id") or register_response.data.get("id")
    assert user_id, f"User ID not found in response: {register_response.data}"

    # Log in to get an access token
    login_data = {"username": "testuser", "password": "testpassword"}
    login_response = api_client.post('/api/v1/auth/login/', login_data)
    assert login_response.status_code == 200, f"User login failed: {login_response.data}"
    
    # Extract the token
    token = login_response.data.get("data", {}).get("access_token") or login_response.data.get("access_token")
    assert token, f"Access token not received: {login_response.data}"
    
    # Set Authorization header for future requests
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    
    # Return both the authenticated client and user ID
    return api_client, user_id


@pytest.fixture
def create_user(db):
    def _create_user(**kwargs):
        return CustomUser.objects.create_user(**kwargs)
    return _create_user