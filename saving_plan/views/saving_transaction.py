from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from django.db import transaction
from django.utils import timezone
from saving_plan.models import SavingsTransaction
from saving_plan.serializers.saving_transaction import SavingsTransactionSerializer

from saving_plan.permissions import IsSavingsPlanUser


class SavingsTransactionListCreateAPIView(APIView):
    permission_classes = [IsSavingsPlanUser]

    def get(self, request):
        queryset = SavingsTransaction.objects.filter(is_deleted=False)
        if not request.user.is_staff:
            queryset = queryset.filter(savings_plan__user=request.user)
        serializer = SavingsTransactionSerializer(
            queryset, many=True, context={"request": request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

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
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SavingsTransactionDetailAPIView(APIView):
    permission_classes = [IsSavingsPlanUser]

    def get_object(self, pk):
        try:
            obj = SavingsTransaction.objects.get(pk=pk, is_deleted=False)
            self.check_object_permissions(self.request, obj)
            return obj
        except SavingsTransaction.DoesNotExist:
            raise NotFound("Transaction not found")

    def get(self, request, pk):
        transaction = self.get_object(pk)
        serializer = SavingsTransactionSerializer(
            transaction, context={"request": request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        transaction = self.get_object(pk)

        if transaction.savings_plan.is_deleted:
            return Response(
                {"error": "Cannot update transaction for a deleted savings plan"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = SavingsTransactionSerializer(
            transaction, data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        transaction = self.get_object(pk)

        if transaction.savings_plan.is_deleted:
            return Response(
                {"error": "Cannot update transaction for a deleted savings plan"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = SavingsTransactionSerializer(
            transaction, data=request.data, partial=True, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        transaction = self.get_object(pk)

        try:
            transaction.is_deleted = True
            transaction.save(update_fields=["is_deleted", "updated_at"])
            return Response(
                {"message": "Transaction deleted successfully"},
                status=status.HTTP_204_NO_CONTENT,
            )
        except Exception as e:
            return Response(
                {"error": "Failed to delete transaction"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
