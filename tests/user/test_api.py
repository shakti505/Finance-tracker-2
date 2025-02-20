
import pytest
from django.test import Client
from user.models import CustomUser
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.urls import reverse
from rest_framework.test import  APIClient

@pytest.mark.parametrize("name,email,username,password,status_code",[
    ("Test User", "test@email.com","testuser","SecurePass123",201),
("Test_user",None,"blank","1234",400)
])
@pytest.mark.django_db
def test_user_registration(api_client,name,username,email,password,status_code):
    url = reverse("user-signup")
    payload = {
        "name": name,
        "email": email,
        "username": username,
        "password": password
    }
    response = api_client.post(url, payload, format="json")
    assert response.status_code == status_code

@pytest.mark.parametrize("username,email,password,status_code",
        [
            ("testuser","test@gmail.com","testpassword",200),
            ("wrong",None,"ksjfkjs",401)
        ],
) 
@pytest.mark.django_db
def test_user_login(api_client, create_user,username,email,password,status_code):
    url = reverse("user-login")
    create_user(email="test@gmail.com", username="testuser", password="testpassword")
    user_name= username
    user_password = password
    payload = {
        "username": user_name,
        "password": user_password
    }
    response = api_client.post(url,payload, format="json")
    print(response.json())
    assert response.status_code == status_code

@pytest.mark.django_db
def test_user_logout(create_user):
    Client = APIClient()
    user = create_user(email="test@gmail.com", username="testuser", password="testpassword")
    url = reverse("user-logout")
    Client.force_authenticate(user=user)
    response = Client.post(url)
    print(response)
    assert response.status_code == 200

@pytest.mark.parametrize("current_password, new_password, confirm_password, status_code",
                        [("testpassword","12345678shakti","12345678shakti",200),
                         ("testpassword","askdbfs","kjasndfs",400)
                         ],)
@pytest.mark.django_db
def test_update_password(authenticated_client,current_password,new_password,confirm_password,status_code):
    # create_user(email="test@gmail.com", username="testuser", password="testpassword")
    api_client, user_id = authenticated_client
    url = reverse("update-password", kwargs={"id": user_id})
    payload = {
    "current_password":current_password,
    "new_password":new_password,
    "confirm_password":confirm_password
}
    response = api_client.post(url,payload)
    response.status_code == status_code




@pytest.mark.django_db
def test_reset_password(mocker, create_user):
    client = Client()
    user_email = "user@example.com"
    create_user(email=user_email, username="testuser", password="Test@123")
    mock_task = mocker.patch("user.tasks.send_email_task.delay")
    response = client.post(
        "/api/v1/auth/password-reset/",
        {"email": user_email},  
    )

    assert response.status_code == 200
    assert response.json() == {"data": {"message": "Password reset email sent."}}

    mock_task.assert_called_once_with(
        ["user@example.com"],
        mocker.ANY
    )



@pytest.mark.parametrize(
    "password, expected_status_code, expected_response",
    [
        ("Weak", 400, {"errors":{"detail": "['This password is too short. It must contain at least 8 characters.']"}}),
        ("password", 400, {"errors":{"detail": "['This password is too common.']"}}),
        ("WeakPassword@1234", 200, {"data":{"message": "Password has been reset successfully."}})
    ],
)
@pytest.mark.django_db
def test_reset_password_confirm(password, expected_status_code, expected_response, mocker, create_user):
    client = Client()

    user_email = "test@email.com"
    username = "testuser"
    user  = create_user(email=user_email, username=username, password="Test@123")
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))

    response = client.post(
        f"/api/v1/auth/password-reset/confirm/{uid}/{token}/",
        {"password": password, "confirm_password": password},
    )

    assert response.status_code == expected_status_code
    assert response.json() == expected_response

    if expected_status_code == 200:
        user.refresh_from_db()
        assert user.check_password(password) == True
        assert user.check_password("Test@1234") == False
    

