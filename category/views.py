from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Category
from .serializers import CategorySerializer
from utils.pagination import CustomPageNumberPagination
from utils.responses import (
    validation_error_response,
    success_response,
    success_single_response,
    not_found_error_response,
    success_no_content_response,
)
from budget.models import Budget
from .swagger_docs import (
    category_list_get_doc,
    category_create_doc,
    category_detail_get_doc,
    category_detail_patch_doc,
    category_detail_delete_doc,
)
from django.shortcuts import get_object_or_404
from utils.permissions import IsStaffOrOwner
from django.db import transaction
from transaction.models import Transaction
from rest_framework.exceptions import NotFound


class CategoryListView(APIView, CustomPageNumberPagination):
    """Handles listing all categories and creating a new category."""

    permission_classes = [IsAuthenticated]

    @category_list_get_doc
    def get(self, request):
        """List all categories for the authenticated user or all categories for staff."""
        category_type = request.query_params.get("type")

        if request.user.is_staff:
            categories = Category.objects.all().order_by("-created_at")
        else:
            categories = Category.objects.filter(
                user=request.user,
                is_deleted=False,
            ).order_by("-created_at") or Category.objects.filter(
                is_predifined=True, is_deleted=False
            ).order_by(
                "-created_at"
            )

        if category_type in ["debit", "credit"]:
            categories = categories.filter(type=category_type)
        paginated_categories = self.paginate_queryset(categories, request)
        serializer = CategorySerializer(paginated_categories, many=True)
        return success_response(
            {
                "count": categories.count(),
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "results": serializer.data,
            }
        )

    @category_create_doc
    def post(self, request):
        """Create a new category for the authenticated user."""

        serializer = CategorySerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return success_single_response(serializer.data, status.HTTP_201_CREATED)
        return validation_error_response(serializer.errors)


class CategoryDetailView(APIView):
    """Handles retrieving, updating, and deleting a specific category."""

    permission_classes = [IsAuthenticated, IsStaffOrOwner]

    def get_object(self, id, request):
        """Retrieve the category object and check permissions."""

        category = get_object_or_404(Category, id=id)
        self.check_object_permissions(request, category)
        return category

    def delete_associated_budgets(self, category):
        """Soft delete all budgets associated with this category and user."""
        # Get all budgets associated with this category
        budgets = Budget.objects.filter(
            category=category, user=category.user, is_deleted=False
        )
        budgets.update(is_deleted=True)

    @category_detail_get_doc
    def get(self, request, id):
        """Retrieve a specific category."""
        try:
            category = self.get_object(id, request)
            serializer = CategorySerializer(category)
            return success_single_response(serializer.data)
        except NotFound:
            return not_found_error_response()

    @category_detail_patch_doc
    def patch(self, request, id):
        """Update a specific category."""
        try:
            category = self.get_object(id, request)
            serializer = CategorySerializer(
                category,
                data=request.data,
                partial=True,
                context={"request": request},
            )
            if serializer.is_valid():
                serializer.save()
                return success_single_response(serializer.data)
            return validation_error_response(serializer.errors)
        except NotFound:
            return not_found_error_response()

    @category_detail_delete_doc
    def delete(self, request, id):
        """Soft-delete a specific category."""
        try:
            category = self.get_object(id, request)
            with transaction.atomic():
                if Transaction.objects.filter(
                    category=category, is_deleted=False
                ).exists():
                    return validation_error_response(
                        {
                            "detail": "Cannot delete category with associated transactions."
                        }
                    )
            category.is_deleted = True
            category.save()
            self.delete_associated_budgets(category)
            return success_no_content_response()
        except NotFound:
            return not_found_error_response()
