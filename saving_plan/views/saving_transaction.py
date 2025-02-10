from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
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
from saving_plan.permissions import IsSavingsPlanUser
from django.shortcuts import get_object_or_404


class SavingsTransactionListCreateAPIView(APIView):
    permission_classes = [IsSavingsPlanUser]

    def get(self, request):
        queryset = SavingsTransaction.objects.filter(is_deleted=False)
        if not request.user.is_staff:
            queryset = queryset.filter(savings_plan__user=request.user)
        serializer = SavingsTransactionSerializer(
            queryset, many=True, context={"request": request}
        )
        return success_response(serializer.data)

    def post(self, request):
        serializer = SavingsTransactionSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            # Check if the related savings plan exists and is not deleted
            savings_plan = serializer.validated_data.get("savings_plan")

            # Check permissions for the savings plan
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
    permission_classes = [IsSavingsPlanUser]

    def get_object(self, id):
        saving_transacion = get_object_or_404(
            SavingsTransaction,
            id=id,
        )
        self.check_object_permissions(self.request, saving_transacion)
        return saving_transacion

    def get(self, request, id):
        transaction = self.get_object(id)
        serializer = SavingsTransactionSerializer(
            transaction, context={"request": request}
        )
        return success_single_response(serializer.data)

    def patch(self, request, pk):
        transaction = self.get_object(id)
        serializer = SavingsTransactionSerializer(
            transaction, data=request.data, context={"request": request}, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return success_single_response(serializer.data)
        return validation_error_response(serializer.errors)

    def delete(self, request, pk):
        transaction = self.get_object(pk)

        try:
            transaction.is_deleted = True
            transaction.save()
            return success_no_content_response()
        except Exception as e:
            return not_found_error_response("Transaction not found.")
