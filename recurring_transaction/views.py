from utils.logging import logger
from rest_framework.views import APIView
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db import transaction as db_transaction
from utils.responses import (
    validation_error_response,
    not_found_error_response,
    success_no_content_response,
    success_single_response,
    success_response,
)
from .models import RecurringTransaction
from .serializers import RecurringTransactionSerializer
from utils.pagination import CustomPageNumberPagination
from utils.permissions import IsStaffOrOwner


class RecurringTransactionListCreateView(APIView, CustomPageNumberPagination):
    """Comprehensive list and create view for recurring transactions"""

    def get(self, request):
        """List recurring transactions with comprehensive filtering"""
        try:
            if request.user.is_staff:
                queryset = RecurringTransaction.objects.all().order_by("-created_at")
            else:
                queryset = RecurringTransaction.objects.filter(
                    user=request.user, is_deleted=False
                ).order_by("-created_at")

            paginated_data = self.paginate_queryset(queryset, request)
            serializer = RecurringTransactionSerializer(paginated_data, many=True)
            logger.info(f"User {request.user.id} retrieved recurring transactions.")
            return success_response(
                {
                    "count": queryset.count(),
                    "next": self.get_next_link(),
                    "previous": self.get_previous_link(),
                    "results": serializer.data,
                }
            )
        except Exception as e:
            logger.error(f"Error fetching recurring transactions: {str(e)}")
            return not_found_error_response("Error fetching recurring transactions.")

    def post(self, request):
        """Create a new recurring transaction"""
        serializer = RecurringTransactionSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            logger.info(f"User {request.user.id} created a new recurring transaction.")
            return success_single_response(
                serializer.data,
                status_code=status.HTTP_201_CREATED,
            )

        logger.warning(f"Validation error: {serializer.errors}")
        return validation_error_response(serializer.errors)


class RecurringTransactionDetailView(APIView):
    """Comprehensive detail view for recurring transactions"""

    permission_classes = [IsStaffOrOwner]

    def get_object(self, id, request):
        """Retrieve recurring transaction with comprehensive permissions"""
        recurring_transaction = get_object_or_404(RecurringTransaction, id=id)
        self.check_object_permissions(request, recurring_transaction)
        return recurring_transaction

    def get(self, request, id):
        """Retrieve specific recurring transaction"""
        try:
            recurring_transaction = self.get_object(id, request)
            serializer = RecurringTransactionSerializer(recurring_transaction)
            logger.info(f"User {request.user.id} retrieved transaction {id}.")
            return success_single_response(serializer.data)
        except Exception as e:
            logger.error(f"Error retrieving transaction {id}: {str(e)}")
            return not_found_error_response("Recurring Transaction not found.")

    def patch(self, request, id):
        """Update specific recurring transaction"""
        try:
            recurring_transaction = self.get_object(id, request)
            serializer = RecurringTransactionSerializer(
                recurring_transaction,
                data=request.data,
                partial=True,
                context={"request": request},
            )
            if serializer.is_valid():
                serializer.save()
                logger.info(f"User {request.user.id} updated transaction {id}.")
                return success_single_response(serializer.data)

            logger.warning(f"Validation error while updating {id}: {serializer.errors}")
            return validation_error_response(serializer.errors)

        except Exception as e:
            logger.error(f"Error updating transaction {id}: {str(e)}")
            return not_found_error_response("Recurring Transaction not found.")

    def delete(self, request, id):
        """Soft delete recurring transaction"""
        try:
            recurring_transaction = self.get_object(id, request)
            with db_transaction.atomic():
                recurring_transaction.is_deleted = True
                recurring_transaction.save()

            logger.info(f"User {request.user.id} deleted transaction {id}.")
            return success_no_content_response()
        except Exception as e:
            logger.error(f"Error deleting transaction {id}: {str(e)}")
            return not_found_error_response("Recurring Transaction not found.")
