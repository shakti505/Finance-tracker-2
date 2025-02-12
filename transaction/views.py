from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from django.shortcuts import get_object_or_404
from .models import Transaction
from .serializers import TransactionSerializer
from utils.responses import (
    validation_error_response,
    success_single_response,
    success_no_content_response,
    not_found_error_response,
    success_response,
)
from utils.pagination import CustomPageNumberPagination
from utils.permissions import IsStaffOrOwner
from .tasks import track_and_notify_budget
from utils.logging import logger
from rest_framework.exceptions import NotFound


class TransactionListCreateView(APIView, CustomPageNumberPagination):
    """API view for listing and creating transactions."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Retrieve all transactions based on user role and query parameters."""
        logger.info("Fetching transactions for user: %s", request.user)
        queryset = (
            Transaction.objects.all().order_by("-created_at")
            if request.user.is_staff
            else Transaction.objects.filter(
                user=request.user, is_deleted=False
            ).order_by("-created_at")
        )

        transaction_type = request.query_params.get("type")
        if transaction_type:
            queryset = queryset.filter(type=transaction_type)

        paginated_data = self.paginate_queryset(queryset, request)
        serializer = TransactionSerializer(paginated_data, many=True)

        logger.info("Transactions retrieved successfully for user: %s", request.user)
        return success_response(
            {
                "count": queryset.count(),
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "results": serializer.data,
            }
        )

    def post(self, request):
        """Create a new transaction."""
        logger.info("Creating a new transaction for user: %s", request.user)
        serializer = TransactionSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            transaction = serializer.save()
            track_and_notify_budget.delay(transaction.id)
            logger.info("Transaction created successfully with ID: %s", transaction.id)
            return success_single_response(
                serializer.data, status_code=status.HTTP_201_CREATED
            )
        logger.error(
            "Transaction creation failed for user: %s. Errors: %s",
            request.user,
            serializer.errors,
        )
        return validation_error_response(serializer.errors)


class TransactionDetailView(APIView):
    """API view for retrieving, updating, and deleting a specific transaction."""

    permission_classes = [IsStaffOrOwner]

    def get_object(self, id, request):
        """Helper method to get the transaction object by primary key with permission check."""
        logger.info("Fetching transaction with ID: %s", id)
        transaction = get_object_or_404(Transaction, id=id)
        self.check_object_permissions(request, transaction)
        return transaction

    def get(self, request, id):
        """Retrieve a specific transaction by its ID."""
        try:
            transaction = self.get_object(id, request)
            serializer = TransactionSerializer(transaction)
            logger.info("Transaction retrieved successfully with ID: %s", id)
            return success_single_response(serializer.data)
        except NotFound:
            logger.error("Transaction not found with ID: %s", id)
            return not_found_error_response(f"No transaction found with ID: {id}")

    def patch(self, request, id):
        """Update a specific transaction."""
        try:

            transaction = self.get_object(id, request)
            serializer = TransactionSerializer(
                transaction,
                data=request.data,
                partial=True,
                context={"request": request},
            )
            if serializer.is_valid():
                updated_transaction = serializer.save()
                track_and_notify_budget.delay(updated_transaction.id)
                logger.info("Transaction updated successfully with ID: %s", id)
                return success_single_response(serializer.data)
            logger.error(
                "Transaction update failed for ID: %s. Errors: %s",
                id,
                serializer.errors,
            )
            return validation_error_response(serializer.errors)
        except NotFound:
            logger.error("Transaction not found with ID: %s", id)
            return not_found_error_response(f"No transaction found with ID: {id}")

    def delete(self, request, id):
        """Delete a specific transaction by ID."""
        try:
            transaction = self.get_object(id, request)
            transaction.is_deleted = True
            transaction.save()
            logger.info("Transaction deleted successfully with ID: %s", id)
            return success_no_content_response()
        except NotFound:
            logger.error("Transaction not found with ID: %s", id)
            return not_found_error_response(f"No transaction found with ID: {id}")
