from celery import shared_task
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from django.db import models
from decimal import Decimal
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from utils.logging import logger
from calendar import monthrange
from saving_plan.models import  SavingsPlan
from transaction.models import Transaction
from services.notification import send_mail
from django.db.models import Sum

# SendGrid template configurations
SENDGRID_TEMPLATES = {
    'PLAN_CREATED': settings.SENDGRID_PLAN_CREATED_TEMPLATE_ID,
    'BEHIND_SCHEDULE': settings.SENDGRID_BEHIND_SCHEDULE_TEMPLATE_ID,
    'GOAL_COMPLETED': settings.SENDGRID_GOAL_COMPLETED_TEMPLATE_ID,
    'OVERDUE':settings.SENDGRID_OVERDUE_TEMPLATE_ID
}

@shared_task
def check_overdue_savings_plans():
    """
    Check for overdue savings plans and apply the hybrid auto-extension approach.
    """
    today = timezone.now().date()

    overdue_plans = SavingsPlan.objects.filter(
        current_deadline__lt=today,
        is_deleted=False,
        status="ACTIVE"
    )

    for plan in overdue_plans:
        total_saved = Transaction.objects.filter(savings_plan=plan).aggregate(total=Sum("amount"))["total"] or Decimal("0")

        # If the user has reached the target amount, mark as completed
        if total_saved >= plan.target_amount:
            plan.status = "COMPLETED"
            plan.save()
            send_savings_plan_completion_notification.delay(plan.id)
            continue
        auto_extend_days = 30 if plan.frequency == "MONTHLY" else 7 if plan.frequency == "WEEKLY" else 1
        new_deadline = plan.current_deadline + timedelta(days=auto_extend_days)

        subject = f"Your Savings Plan {plan.name} Deadline Passed - Auto-Extension in Progress"

        dynamic_template_data = {
            "user_name": plan.user.name,
            "plan_name": plan.name,
            "deadline": plan.current_deadline.strftime("%Y-%m-%d"),
            "new_deadline": new_deadline.strftime("%Y-%m-%d"),
            "target_amount": f"{plan.target_amount:,.2f}",
            "total_saved": f"{total_saved:,.2f}",
            "remaining_amount": f"{plan.target_amount - total_saved:,.2f}",
            "message": (
                f"Your savings plan deadline has passed, and we are extending it automatically to {new_deadline.strftime('%Y-%m-%d')}."
            ),
        }
        
        send_mail(
            [plan.user.email],
            subject,
            dynamic_template_data=dynamic_template_data,
            dynamic_template_id=SENDGRID_TEMPLATES["OVERDUE"],
        )

        # Automatically extend deadline unless the user opts out
        plan.current_deadline = new_deadline
        plan.save()

@shared_task
def check_savings_progress():
    """Ensure users are meeting their periodic savings targets based on remaining time."""
    today = timezone.now().date()

    plans = SavingsPlan.objects.filter(
        is_deleted=False,
        status="ACTIVE",
        current_deadline__gte=today
    ).annotate(
        total_saved=Sum("transactions__amount")
    ).filter(
        total_saved__lt=models.F("target_amount")
    )

    for plan in plans:
        total_saved = plan.total_saved or Decimal("0")
        remaining_amount = plan.target_amount - total_saved

        days_remaining = (plan.current_deadline - today).days
        if days_remaining <= 0 or remaining_amount <= 0:
            continue

        if plan.frequency == "MONTHLY":
            remaining_periods = max((days_remaining + 29) // 30, 1)
            required_per_period = remaining_amount / remaining_periods
            period_start = today.replace(day=1)
        elif plan.frequency == "WEEKLY":
            remaining_periods = max((days_remaining + 6) // 7, 1)
            required_per_period = remaining_amount / remaining_periods
            period_start = today - timedelta(days=today.weekday())
        elif plan.frequency == "DAILY":
            required_per_period = remaining_amount / max(days_remaining, 1)
            period_start = today

        period_savings = Transaction.objects.filter(
            savings_plan=plan,
            date__gte=period_start,
            date__lte=today
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0")

        if period_savings < required_per_period:
            dynamic_template_data = {
                "user_name": plan.user.name,
                "plan_name": plan.name,
                "target_amount": f"{plan.target_amount:,.2f}",
                "total_saved": f"{total_saved:,.2f}",
                "remaining_amount": f"{remaining_amount:,.2f}",
                "required_per_period": f"{required_per_period:,.2f}",
                "saved_this_period": f"{period_savings:,.2f}",
                "shortfall": f"{max(required_per_period - period_savings, 0):,.2f}",
                "frequency": plan.frequency.lower(),
                "days_remaining": days_remaining,
                "message": (
                    f"You need to save {required_per_period:.2f} per {plan.frequency.lower()} "
                    f"to meet your goal by {plan.current_deadline}."
                )
            }
            send_mail(
                [plan.user.email],
                f"Reminder: You need to save {required_per_period:.2f} for {plan.name}",
                dynamic_template_data=dynamic_template_data,
                dynamic_template_id=SENDGRID_TEMPLATES["BEHIND_SCHEDULE"]
            )
@shared_task
def send_savings_plan_creation_notification(plan_id):
    """Send notification when a new savings plan is created."""
    try:
        plan = SavingsPlan.objects.get(id=plan_id)
        
        template_data = {
            'user_name': plan.user.name,
            'plan_name': plan.name,
            'target_amount': f"{float(plan.target_amount):,.2f}",
            'frequency': plan.frequency,
            'deadline': plan.current_deadline.strftime('%Y-%m-%d')
        }


        send_mail(
            [plan.user.email],
            "New Savings Plan Created!",
            dynamic_template_data=template_data,
            dynamic_template_id=SENDGRID_TEMPLATES['PLAN_CREATED']
        )
    except Exception as e:
        logger.error(f"Failed to send creation notification for plan {plan_id}: {str(e)}")



@shared_task
def delete_related(savings_plan_id):
    """
    Celery task to handle soft deletion of extension models.
    """
    saving_plan = SavingsPlan.objects.filter(
        savings_plan_id=savings_plan_id
    ).first()
    
    with transaction.atomic():
        Transaction.objects.filter(saving_plan=saving_plan).update(
            is_deleted=True
        )
    return f"Successfully processed extensions for soft deletion"


@shared_task
def send_savings_plan_completion_notification(plan_id):
    """Send a notification when a savings plan is completed."""

    plan = SavingsPlan.objects.get(id=plan_id)

    template_data = {
        'user_name': plan.user.name,
        'plan_name': plan.name,
        'total_saved': f"{float(plan.target_amount):,.2f}",
        'completion_date': timezone.now().date().strftime('%Y-%m-%d')
    }

    send_mail(
        [plan.user.email],
        "Congratulations! Savings Plan Completed",
        dynamic_template_data=template_data,
        dynamic_template_id=SENDGRID_TEMPLATES['GOAL_COMPLETED']
    )
@shared_task
def schedule_savings_checks():
    """Main task to be scheduled that coordinates all notifications."""
    check_savings_progress.delay()
    check_overdue_savings_plans.delay()
