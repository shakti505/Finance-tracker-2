from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import transaction
from django.utils import timezone
from saving_plan.models import SavingsTransaction
from saving_plan.serializers.saving_transaction import SavingsTransactionSerializer
from utils.responses import (
    success_response,
    not_found_error_response,
    success_single_response,
    validation_error_response,
    success_no_content_response,
)
from django.shortcuts import get_object_or_404
from utils.pagination import CustomPageNumberPagination
from rest_framework.permissions import IsAuthenticated
from utils.permissions import IsStaffOrOwner


class SavingsTransactionListCreateAPIView(APIView, CustomPageNumberPagination):
    permission_classes = [IsStaffOrOwner, IsAuthenticated]

    def get(self, request):
        queryset = SavingsTransaction.objects.filter()
        if not request.user.is_staff:
            queryset = queryset.filter(user=request.user, is_deleted=False)
        paginated_queryset = self.paginate_queryset(queryset, request)
        serializer = SavingsTransactionSerializer(
            paginated_queryset, many=True, context={"request": request}
        )

        return success_response(
            {
                "count": queryset.count(),
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "results": serializer.data,
            }
        )

    def post(self, request):
        serializer = SavingsTransactionSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            # Check if the related savings plan exists and is not deleted
            savings_plan = serializer.validated_data.get("savings_plan")
            self.check_object_permissions(request, savings_plan)
            if savings_plan.is_deleted:
                return Response(
                    {"error": "Cannot create transaction for a deleted savings plan"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            serializer.save(user=request.user)
            return success_single_response(
                serializer.data, status_code=status.HTTP_201_CREATED
            )
        return validation_error_response(
            serializer.errors,
        )


class SavingsTransactionDetailAPIView(APIView):
    permission_classes = [IsStaffOrOwner, IsAuthenticated]

    def get_object(self, id):
        saving_transacion = get_object_or_404(
            SavingsTransaction,
            id=id,
        )
        self.check_object_permissions(self.request, saving_transacion)
        return saving_transacion

    def get(self, request, id):
        try:
            transaction = self.get_object(id)
        except Exception:
            return not_found_error_response("Transaction not found.")
        serializer = SavingsTransactionSerializer(
            transaction, context={"request": request}
        )
        return success_single_response(serializer.data)

    def patch(self, request, id):
        try:
            transaction = self.get_object(id)
        except Exception:
            return not_found_error_response("Transaction not found.")
        serializer = SavingsTransactionSerializer(
            transaction,
            data=request.data,
            context={"request": request},
            partial=True,
        )
        if serializer.is_valid():
            serializer.save()
            return success_single_response(serializer.data)
        return validation_error_response(serializer.errors)

    def delete(self, request, id):
        try:
            transaction = self.get_object(id)
        except Exception:
            return not_found_error_response("Transaction not found.")
        transaction.is_deleted = True
        transaction.save()
        return success_no_content_response()
