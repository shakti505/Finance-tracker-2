from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from .serializers import CategorySerializer

# 📌 Swagger Documentation for Listing Categories
category_list_get_doc = swagger_auto_schema(
    operation_summary="List All Categories",
    operation_description="Retrieve all categories for the authenticated user. Staff can view all categories.",
    manual_parameters=[
        openapi.Parameter(
            "type",
            openapi.IN_QUERY,
            description="Filter categories by type (debit or credit).",
            type=openapi.TYPE_STRING,
        ),
    ],
    responses={
        200: CategorySerializer(many=True),
        400: openapi.Response("Bad request"),
    },
)

# 📌 Swagger Documentation for Creating a Category
category_create_doc = swagger_auto_schema(
    operation_summary="Create a New Category",
    operation_description="Creates a new category for the authenticated user.",
    request_body=CategorySerializer,
    responses={
        201: CategorySerializer,
        400: openapi.Response("Validation error"),
    },
)

# 📌 Swagger Documentation for Retrieving a Category
category_detail_get_doc = swagger_auto_schema(
    operation_summary="Retrieve a Specific Category",
    operation_description="Fetch details of a specific category by ID.",
    responses={
        200: CategorySerializer,
        404: openapi.Response("Category not found"),
    },
)

# 📌 Swagger Documentation for Updating a Category
category_detail_patch_doc = swagger_auto_schema(
    operation_summary="Update a Category",
    operation_description="Update an existing category.",
    request_body=CategorySerializer,
    responses={
        200: CategorySerializer,
        400: openapi.Response("Validation error"),
        404: openapi.Response("Category not found"),
    },
)

# 📌 Swagger Documentation for Deleting a Category
category_detail_delete_doc = swagger_auto_schema(
    operation_summary="Soft Delete a Category",
    operation_description="Marks a category as deleted instead of permanently removing it. Also soft deletes associated budgets.",
    responses={
        204: openapi.Response("Category deleted successfully"),
        404: openapi.Response("Category not found"),
    },
)
