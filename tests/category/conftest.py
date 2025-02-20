import pytest
from django.urls import reverse

@pytest.fixture
def create_category(db, authenticated_client):
    """Creates a category and returns its ID"""
    api_client, user_id = authenticated_client
    # url = reverse("category-list-create")  # Ensure this matches your `urls.py`
    
    payload = {
        "user": user_id,
        "type": "DEBIT",
        "name": "Travel"
    }

    response = api_client.post(f"/api/v1/categories/", payload)
    
    assert response.status_code == 201, f"Failed to create category: {response.data}"

    category_id = response.data.get("data", {}).get("id") or response.data.get("id")
    assert category_id, f"Category ID was not returned in response: {response.data}"

    return category_id

