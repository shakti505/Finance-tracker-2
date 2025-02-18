import pytest 


# @pytest.mark.django_db
# def test_user_creation():
#     payload = dict(
#         name = "testusers",
#         username = "test123",
#         email = "test@email.com",
#         password = "test@123344",
#     )
#     response = client.post("/api/v1/auth/register/", payload)
#     assert response.status_code == 201
#     data = response.data.get("data", {}) 
#     assert data["name"] == payload["name"]
#     assert data["username"] == payload["username"]
#     assert data["email"] == payload["email"]
    # assert "password" not in data

# import pytest
# from rest_framework.test import APIClient
# client = APIClient()

# @pytest.mark.django_db
# def test_user_login():
#     # Create the user first if not already in the database
#     payload_create = dict(
#         name="shakti user",
#         username="shakti_user",  # Ensure username matches the one used for login
#         email="shakti@domain.com",
#         password="shakti@1234",  # Same password used during login attempt
#     )
    
#     # Register the user
#     client.post("/api/v1/auth/register/", payload_create)

#     # Now try logging in with the created user's credentials
#     payload_login = dict(
#         username="shakti_user",  # Correct username
#         password="shakti@1234",  # Correct password
#     )

#     # Send login request
#     response = client.post("/api/v1/auth/login/", payload_login)

#     # Check the status code of the response
#     print(f"Response status code: {response.status_code}")  # To see the status code
#     print(f"Response content: {response.content}")  # To print the full response body

#     # Assert status code is 200, meaning the login was successful
#     assert response.status_code == 200, f"Expected status 200, but got {response.status_code}"

#     # Check that we get the expected data (e.g., token or user info)
#     data = response.data.get("data", {})
    
#     # Ensure the data is as expected
#     assert "access_token" and "refresh_token" in data



@pytest.mark.django_db
def test_user_logout(api_client):
    response = api_client.post("/api/v1/auth/logout/")
    assert response.status_code == 200