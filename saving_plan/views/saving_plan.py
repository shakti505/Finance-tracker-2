from rest_framework import status
from rest_framework.views import APIView
from saving_plan.models import SavingsPlan
from saving_plan.serializers.saving_plan import SavingsPlanSerializer
from utils.permissions import IsStaffOrOwner
from utils.responses import (
    success_response,
    not_found_error_response,
    success_single_response,
    validation_error_response,
    success_no_content_response,
)
from django.shortcuts import get_object_or_404
from saving_plan.tasks import delete_related
from utils.logging import logger
from utils.pagination import CustomPageNumberPagination
from rest_framework.permissions import IsAuthenticated


class SavingsPlanListCreateAPIView(APIView, CustomPageNumberPagination):
    permission_classes = [IsStaffOrOwner, IsAuthenticated]

    def get(self, request):
        logger.info("Fetching savings plans for user: %s", request.user)
        queryset = SavingsPlan.objects.filter()
        if not request.user.is_staff:
            queryset = queryset.filter(user=request.user, is_deleted=False)

        paginated_queryset = self.paginate_queryset(queryset, request)
        serializer = SavingsPlanSerializer(
            queryset, many=True, context={"request": request}
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
        logger.info("Creating a new savings plan for user: %s", request.user)
        serializer = SavingsPlanSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            logger.info("Savings plan created successfully for user: %s", request.user)
            return success_single_response(
                serializer.data, status_code=status.HTTP_201_CREATED
            )
        logger.warning(
            "Validation error while creating savings plan: %s", serializer.errors
        )
        return validation_error_response(serializer.errors)


class SavingsPlanDetailAPIView(APIView):
    permission_classes = [IsStaffOrOwner, IsAuthenticated]

    def get_object(self, id):
        logger.info("Fetching savings plan with ID: %s", id)
        obj = get_object_or_404(SavingsPlan, id=id)
        self.check_object_permissions(self.request, obj)
        return obj

    def get(self, request, id):
        try:
            plan = self.get_object(id)
            logger.info("Fetched savings plan: %s", id)
        except Exception as e:
            logger.error("Savings plan not found: %s, Error: %s", id, str(e))
            return not_found_error_response()
        serializer = SavingsPlanSerializer(plan, context={"request": request})
        return success_single_response(serializer.data)

    def patch(self, request, id):
        try:
            plan = self.get_object(id)
            logger.info("Updating savings plan: %s", id)
        except Exception as e:
            logger.error("Savings plan not found for update: %s, Error: %s", id, str(e))
            return not_found_error_response()
        was_completed = plan.is_completed
        serializer = SavingsPlanSerializer(
            plan, data=request.data, partial=True, context={"request": request}
        )
        if serializer.is_valid():
            updated_plan = serializer.save()

            if was_completed != updated_plan.is_completed:
                logger.info(
                    "Savings plan completion status changed from %s to %s: %s",
                    was_completed,
                    updated_plan.is_completed,
                    id,
                )
            return success_single_response(serializer.data)
        logger.warning(
            "Validation error while updating savings plan: %s, Errors: %s",
            id,
            serializer.errors,
        )
        return validation_error_response(serializer.errors)

    def delete(self, request, id):
        try:
            plan = self.get_object(id)
            logger.info("Soft deleting savings plan: %s", id)
        except Exception as e:
            logger.error(
                "Savings plan not found for deletion: %s, Error: %s", id, str(e)
            )
            return not_found_error_response()

        plan.is_deleted = True
        plan.save()
        delete_related.delay(plan.id)
        logger.info("Savings plan soft deleted successfully: %s", id)
        return success_no_content_response()
