from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from django.db import transaction
from django.utils import timezone
from saving_plan.models import SavingsPlan, SavingsTransaction
from saving_plan.serializers.saving_plan import SavingsPlanSerializer
from saving_plan.permissions import IsSavingsPlanUser
from utils.responses import (
    success_response,
    not_found_error_response,
    success_single_response,
    validation_error_response,
    success_no_content_response,
    success_single_response,
)
from django.shortcuts import get_object_or_404


class SavingsPlanListCreateAPIView(APIView):
    permission_classes = [IsSavingsPlanUser]

    def get(self, request):
        queryset = SavingsPlan.objects.filter()
        if not request.user.is_staff:
            queryset = queryset.filter(user=request.user, is_deleted=False)
        serializer = SavingsPlanSerializer(
            queryset, many=True, context={"request": request}
        )
        return success_response(
            serializer.data,
        )

    def post(self, request):
        serializer = SavingsPlanSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return success_single_response(
                serializer.data, status_code=status.HTTP_201_CREATED
            )
        return validation_error_response(serializer.errors)


class SavingsPlanDetailAPIView(APIView):
    permission_classes = [IsSavingsPlanUser]

    def get_object(self, id):
        obj = get_object_or_404(SavingsPlan, id=id)
        self.check_object_permissions(self.request, obj)
        return obj

    def get(self, request, id):
        plan = self.get_object(id)
        serializer = SavingsPlanSerializer(plan, context={"request": request})
        return success_single_response(
            serializer.data,
        )

    def patch(self, request, id):
        plan = self.get_object(id)
        serializer = SavingsPlanSerializer(
            plan, data=request.data, partial=True, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return success_single_response(serializer.data)
        return validation_error_response(serializer.errors)

    @transaction.atomic
    def delete(self, request, id):
        plan = self.get_object(id)

        try:
            # Update all related transactions
            SavingsTransaction.objects.filter(
                savings_plan=plan, is_deleted=False
            ).update(is_deleted=True, updated_at=timezone.now())

            plan.is_deleted = True
            plan.save(update_fields=["is_deleted", "updated_at"])

            return success_no_content_response()
        except Exception as e:
            return Response(
                {"error": "Failed to delete plan and related transactions"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
