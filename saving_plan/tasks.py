from celery import shared_task
from django.db import transaction
from saving_plan.models import DeadlineExtension


@shared_task
def delete_related(savings_plan):
    """
    Celery task to handle soft deletion of extension models.
    """
    try:
        with transaction.atomic():
            # Import your Extension model here to avoid circular imports

            DeadlineExtension.objects.filter(
                savings_plan=savings_plan,
                is_deleted=True,
            ).update(is_deleted=True)

        return f"Successfully processed extensions for soft deletion"
    except Exception as e:
        return f"Error processing soft delete: {str(e)}"
