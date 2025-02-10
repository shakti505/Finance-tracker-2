from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from .serializers import BudgetSerializer

# 📌 Swagger Documentation for Listing Budgets
budget_list_get_doc = swagger_auto_schema(
    operation_summary="List All Budgets",
    operation_description="Retrieve all budgets with optional filters (category, month-year).",
    manual_parameters=[
        openapi.Parameter(
            "category",
            openapi.IN_QUERY,
            description="Filter by category ID",
            type=openapi.TYPE_INTEGER,
        ),
        openapi.Parameter(
            "month_year",
            openapi.IN_QUERY,
            description="Filter by month-year in MM-YYYY format",
            type=openapi.TYPE_STRING,
        ),
    ],
    responses={
        200: BudgetSerializer(many=True),
        400: openapi.Response("Invalid filter format"),
        500: openapi.Response("Internal server error"),
    },
)

# 📌 Swagger Documentation for Creating a Budget
budget_create_doc = swagger_auto_schema(
    operation_summary="Create a New Budget",
    operation_description="Creates a new budget entry.",
    request_body=BudgetSerializer,
    responses={
        201: BudgetSerializer,
        400: openapi.Response("Validation error"),
    },
)

# 📌 Swagger Documentation for Retrieving a Budget
budget_detail_get_doc = swagger_auto_schema(
    operation_summary="Retrieve a Specific Budget",
    operation_description="Fetch details of a specific budget by ID.",
    responses={
        200: BudgetSerializer,
        404: openapi.Response("Budget not found"),
    },
)

# 📌 Swagger Documentation for Updating a Budget
budget_detail_patch_doc = swagger_auto_schema(
    operation_summary="Update a Budget",
    operation_description="Update an existing budget entry.",
    request_body=BudgetSerializer,
    responses={
        200: BudgetSerializer,
        400: openapi.Response("Validation error"),
        404: openapi.Response("Budget not found"),
    },
)

# 📌 Swagger Documentation for Deleting a Budget
budget_detail_delete_doc = swagger_auto_schema(
    operation_summary="Soft Delete a Budget",
    operation_description="Marks a budget entry as deleted instead of permanently removing it.",
    responses={
        204: openapi.Response("Budget deleted successfully"),
        404: openapi.Response("Budget not found"),
    },
)
