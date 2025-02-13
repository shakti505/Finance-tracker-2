from celery import shared_task
from django.db import transaction
from saving_plan.models import DeadlineExtension, SavingsTransaction
from django.utils import timezone
from django.conf import settings
from saving_plan.models import SavingsPlan
from services.notification import send_mail


@shared_task
def delete_related(savings_plan_id):
    """
    Celery task to handle soft deletion of extension models.
    """
    saving_plan = SavingsTransaction.objects.filter(
        savings_plan_id=savings_plan_id
    ).first()
    with transaction.atomic():
        SavingsTransaction.objects.filter(saving_plan=saving_plan).update(
            is_deleted=True
        )
        DeadlineExtension.objects.filter(
            saving_plan=saving_plan,
        ).update(is_deleted=True)
    return f"Successfully processed extensions for soft deletion"


@shared_task
def check_overdue_savings_plans():
    """
    Check for overdue savings plans and send email notifications.
    """
    # Query for overdue plans
    overdue_plans = SavingsPlan.objects.filter(
        current_deadline__lt=timezone.now().date(),
    )
    extend_deadline_link = (
        f"http://127.0.0.1:8000/api/v1/savings-plans/extend-deadline/"
    )

    # Send email for each overdue plan
    for plan in overdue_plans:
        subject = f"Savings Plan Deadline Crossed: {plan.name}"

        dynamic_template_data = {
            "subject": subject,
            "user_name": plan.user.name,
            "plan_name": plan.name,
            "deadline": plan.current_deadline.strftime("%Y-%m-%d"),
            "target_amount": f"{plan.target_amount:,.2f}",
            "extend_deadline_link": extend_deadline_link,
        }

        send_mail(
            [plan.user.email],
            subject,
            dynamic_template_data=dynamic_template_data,
            dynamic_template_id=settings.SENDGRID_OVERDUE_TEMPLATE_ID,
        )
