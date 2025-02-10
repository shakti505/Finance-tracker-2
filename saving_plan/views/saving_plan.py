from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from django.db import transaction
from django.utils import timezone
from saving_plan.models import SavingsPlan, SavingsTransaction
from saving_plan.serializers.saving_plan import SavingsPlanSerializer
from saving_plan.permissions import IsSavingsPlanUser


class SavingsPlanListCreateAPIView(APIView):
    permission_classes = [IsSavingsPlanUser]

    def get(self, request):
        queryset = SavingsPlan.objects.filter(is_deleted=False)
        if not request.user.is_staff:
            queryset = queryset.filter(user=request.user)
        serializer = SavingsPlanSerializer(
            queryset, many=True, context={"request": request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = SavingsPlanSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SavingsPlanDetailAPIView(APIView):
    permission_classes = [IsSavingsPlanUser]

    def get_object(self, pk):
        try:
            obj = SavingsPlan.objects.get(pk=pk, is_deleted=False)
            self.check_object_permissions(self.request, obj)
            return obj
        except SavingsPlan.DoesNotExist:
            raise NotFound("Savings plan not found")

    def get(self, request, pk):
        plan = self.get_object(pk)
        serializer = SavingsPlanSerializer(plan, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        plan = self.get_object(pk)
        serializer = SavingsPlanSerializer(
            plan, data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        plan = self.get_object(pk)
        serializer = SavingsPlanSerializer(
            plan, data=request.data, partial=True, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @transaction.atomic
    def delete(self, request, pk):
        plan = self.get_object(pk)

        try:
            # Update all related transactions
            SavingsTransaction.objects.filter(
                savings_plan=plan, is_deleted=False
            ).update(is_deleted=True, updated_at=timezone.now())

            # Update the savings plan
            plan.is_deleted = True
            plan.save(update_fields=["is_deleted", "updated_at"])

            return Response(
                {"message": "Plan and all related transactions deleted successfully"},
                status=status.HTTP_204_NO_CONTENT,
            )
        except Exception as e:
            return Response(
                {"error": "Failed to delete plan and related transactions"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
