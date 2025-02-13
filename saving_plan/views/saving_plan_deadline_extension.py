from rest_framework import status
from rest_framework.views import APIView
from saving_plan.models import SavingsPlan
from saving_plan.serializers.saving_plan_deadline_extension import (
    ExtendDeadlineSerializer,
)
from saving_plan.serializers.saving_plan import SavingsPlanSerializer
from utils.permissions import IsStaffOrOwner
from utils.responses import (
    success_single_response,
    validation_error_response,
    success_response,
    not_found_error_response,
)
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from utils.logging import logger
from saving_plan.models import DeadlineExtension


class ExtendDeadlineAPIView(APIView):
    permission_classes = [IsStaffOrOwner, IsAuthenticated]

    def get_object(self, id):
        obj = get_object_or_404(SavingsPlan, id=id)
        self.check_object_permissions(self.request, obj)
        return obj

    def get(self, request):
        try:
            savings_plan_id = request.query_params.get("savings_plan")
            if not savings_plan_id:
                return validation_error_response("savings_plan parameter is required")

            savings_plan = get_object_or_404(SavingsPlan, id=savings_plan_id)
            self.check_object_permissions(request, savings_plan)
        except Exception:
            logger.warning("Savings plan not found")
            return not_found_error_response("Savings plan not found")

        extensions = DeadlineExtension.objects.filter(
            savings_plan=savings_plan
        ).order_by("-created_at")
        logger.info(
            f"Fetched {extensions.count()} extensions for savings plan: {savings_plan.id}"
        )

        return success_response(ExtendDeadlineSerializer(extensions, many=True).data)

    def post(self, request):
        id = request.data.get("savings_plan")
        if not id:
            return validation_error_response("savings_plan parameter is required")
        try:

            plan = self.get_object(id)
        except Exception:
            logger.warning("Savings plan not found")
            return not_found_error_response("Savings plan not found")
        logger.info(f"Extending deadline for savings plan: {plan.id}")
        serializer = ExtendDeadlineSerializer(
            data=request.data, context={"request": request, "savings_plan": plan}
        )
        if serializer.is_valid():
            extension = serializer.save()
            logger.info(f"Deadline extended successfully for plan: {plan.id}")
            return success_single_response(SavingsPlanSerializer(plan).data)
        logger.warning(f"Validation error: {serializer.errors}")
        return validation_error_response(serializer.errors)
