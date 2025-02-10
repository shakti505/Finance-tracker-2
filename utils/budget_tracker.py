# utils/budget_tracker.py

from budget.models import Budget
from django.db.models import Sum
from decimal import Decimal
from services.notification import NotificationService


from datetime import datetime, timedelta


def track_budget_limit(transaction):
    """Track the budget and check if the limit is reached."""
    try:
        # Get the budget for the category and time of the transaction
        budget = Budget.objects.get(
            user=transaction.user,
            category=transaction.category,
            year=transaction.date.year,
            month=transaction.date.month,
        )

        # Calculate the total spending for the category and time period
        total_spent = transaction.__class__.objects.filter(
            user=transaction.user,
            category=transaction.category,
            date__year=transaction.date.year,
            date__month=transaction.date.month,
            is_deleted=False,
        ).aggregate(Sum("amount"))["amount__sum"] or Decimal("0")

        # Check if the spending has exceeded any thresholds
        if total_spent >= budget.amount:
            send_budget_alert(budget, total_spent, transaction.amount)

        # Check for warning and critical thresholds
        if total_spent >= budget.CRITICAL_THRESHOLD:
            send_budget_alert(budget, total_spent, transaction.amount, critical=True)
        elif total_spent >= budget.WARNING_THRESHOLD and budget.was_below_warning:
            send_budget_alert(budget, total_spent, transaction.amount)

        # Update the last warning sent time after notifying
        budget.last_warning_sent_at = datetime.now()
        budget.save()

    except Budget.DoesNotExist:
        pass  # No budget for this category/time, so do nothing


def send_budget_alert(budget, total_spent, new_spent, critical=False):
    """Send an email notification if the budget limit is reached or exceeded."""
    percentage = (total_spent / budget.amount) * 100
    subject = f"Budget Alert: {budget.category.name} - {percentage:.1f}% used"

    # If critical, mention in the subject line
    if critical:

        subject = (
            f"CRITICAL Budget Alert: {budget.category.name} - {percentage:.1f}% used"
        )

    # Prepare the email content
    content = (
        f"You have used {total_spent} out of {budget.amount} for category {budget.category.name}."
        f"\nCurrent spending is {new_spent}. Budget status: {'Critical' if critical else 'Warning'}."
    )

    # Send the email
    NotificationService.send_budget_alert(
        user_email=budget.user.email,
        category_name=budget.category.name,
        percentage=percentage,
        amount=budget.amount,
        spent=total_spent,
        subject=subject,
        content=content,
    )

    # Update the flag indicating whether the spending was below warning threshold
    if total_spent >= budget.WARNING_THRESHOLD:
        budget.was_below_warning = False
        budget.save()
