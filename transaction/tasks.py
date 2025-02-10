# utils/tasks.py
from celery import shared_task
from django.utils import timezone
from budget.models import Budget
from transaction.models import Transaction
from services.notification import send_mail
from django.db.models import Sum
from decimal import Decimal
from django.conf import settings


@shared_task
def track_and_notify_budget(transaction_id):
    """
    Asynchronously track the budget and send a notification if the limit is reached.
    """
    try:
        # Fetch the transaction from the database by ID
        transaction = Transaction.objects.get(id=transaction_id)

        # Get the budget for the category and time of the transaction
        budget = Budget.objects.filter(
            user=transaction.user,
            category=transaction.category,
            year=transaction.date.year,
            month=transaction.date.month,
            is_deleted=False,
        ).first()
        if not budget:
            return
        # Calculate the total spending for the category and time period
        total_spent = Transaction.objects.filter(
            user=transaction.user,
            category=transaction.category,
            date__year=transaction.date.year,
            date__month=transaction.date.month,
            is_deleted=False,
        ).aggregate(Sum("amount"))["amount__sum"] or Decimal("0")

        # Check if the spending has exceeded any thresholds
        total_spent_percentage = (total_spent / budget.amount) * 100

        # Check for warning and critical thresholds
        if total_spent_percentage >= budget.CRITICAL_THRESHOLD:
            send_budget_alert(budget, total_spent, transaction.amount, critical=True)
        elif total_spent_percentage >= budget.WARNING_THRESHOLD:
            send_budget_alert(budget, total_spent, transaction.amount)
        budget.save()

    except Budget.DoesNotExist:
        pass  # No budget for this category/time, so do nothing


def send_budget_alert(budget, total_spent, critical=False):
    """Send an email notification if the budget limit is reached or exceeded."""
    percentage = (total_spent / budget.amount) * 100

    # Define the subject line based on the severity level
    if critical:
        subject = f"⚠️ CRITICAL: Budget Limit Exceeded for {budget.category.name}"
    else:
        subject = f"⚠️ Warning: Budget Usage High for {budget.category.name}"

    # Prepare dynamic template data
    dynamic_template_data = {
        "subject": subject,
        "user_name": budget.user.name,
        "total_spent": f"{total_spent:,.2f}",
        "budget_amount": f"{budget.amount:,.2f}",
        "category_name": budget.category.name,
        "percentage": f"{percentage:.1f}",
        "critical": critical,
    }

    # Send the email using SendGrid
    send_mail(
        user_email=budget.user.email,
        subject=subject,
        dynamic_template_data=dynamic_template_data,
        dynamic_template_id=settings.SENDGRID_BUDGET_ALERT_TEMPLATE_ID,
    )
