from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from django.db import transaction
from django.utils import timezone
from saving_plan.models import SavingsPlan, SavingsTransaction
from saving_plan.serializers.saving_plan_deadline_extension import (
    ExtendDeadlineSerializer,
)
from saving_plan.serializers.saving_plan import SavingsPlanSerializer
from saving_plan.permissions import IsSavingsPlanUser


class ExtendDeadlineAPIView(APIView):
    permission_classes = [IsSavingsPlanUser]

    def get_object(self, request):
        try:
            id = request.data.get("savings_plan")
            print(id)

            obj = SavingsPlan.objects.get(id=id, is_deleted=False)
            self.check_object_permissions(request, obj)
            return obj
        except SavingsPlan.DoesNotExist:
            raise NotFound("Plan not found")

    def post(self, request):
        plan = self.get_object(request)
        print(request.data)
        serializer = ExtendDeadlineSerializer(
            data=request.data, context={"request": request, "savings_plan": plan}
        )
        if serializer.is_valid():
            extension = serializer.save()
            return Response(SavingsPlanSerializer(plan).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
