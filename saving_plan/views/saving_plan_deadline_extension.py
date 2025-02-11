from rest_framework import status
from rest_framework.views import APIView
from rest_framework.exceptions import NotFound

from saving_plan.models import SavingsPlan
from saving_plan.serializers.saving_plan_deadline_extension import (
    ExtendDeadlineSerializer,
)

from saving_plan.serializers.saving_plan import SavingsPlanSerializer
from saving_plan.permissions import IsSavingsPlanUser
from utils.responses import (
    success_single_response,
    validation_error_response,
    success_response,
)


class ExtendDeadlineAPIView(APIView):
    permission_classes = [IsSavingsPlanUser]

    def get_object(self, request):
        try:
            obj = SavingsPlan.objects.get(
                pk=request.data.get("savings_plan"), is_deleted=False
            )
            self.check_object_permissions(request, obj)
            return obj
        except SavingsPlan.DoesNotExist:
            raise NotFound("Savings plan not found")

    def get(self, request):
        plan = self.get_object(request)
        return success_response(SavingsPlanSerializer(plan, many=True).data)

    def post(self, request):
        plan = self.get_object(request)
        print(request.data)
        serializer = ExtendDeadlineSerializer(
            data=request.data, context={"request": request, "savings_plan": plan}
        )
        if serializer.is_valid():
            extension = serializer.save()
            return success_single_response(SavingsPlanSerializer(plan).data)
        return validation_error_response(serializer.errors)
