import pytest
from django.urls import reverse

# @pytest.mark.django_db
# def test_create_category(authenticated_client):
#     url = reverse("category-list-create")
#     api_client, user_id = authenticated_client
#     payload = {
#         "user":user_id,
#         "type":"DEBIT",
#         "name":"Travel"
#     }
#     response = api_client.post(url,payload)
#     response.status_code == 201

@pytest.mark.django_db
def test_get_categories(authenticated_client, create_category):
    category_id = create_category
    api_client, _ = authenticated_client
    response = api_client.get(f"/api/v1/categories/")
    assert response.status_code == 200

@pytest.mark.django_db
def test_get_category(authenticated_client, create_category):
    """Tests retrieving a category by ID"""
    category_id = create_category
    api_client, _ = authenticated_client
    response = api_client.get(f"/api/v1/categories/{category_id}/")
    assert response.status_code == 200

@pytest.mark.django_db
def test_update_category(authenticated_client, create_category):
    category_id = create_category
    api_client, user_id = authenticated_client
    payload = {
        "name":"Travel 2"
    }
    response = api_client.patch(f"/api/v1/categories/{category_id}/",payload)
    assert response.status_code == 200