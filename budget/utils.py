from django.conf import settings
from decimal import Decimal
from django.db.models import Sum
from services.notification import send_mail
from .models import Budget
from transaction.models import Transaction


def monitor_budget_and_notify(budget):
    user = budget.user
    category = budget.category
    month = budget.month
    year = budget.year
    try:
        total_spent = Transaction.objects.filter(
            user=user,
            category=category,
            date__year=year,
            date__month=month,
            is_deleted=False,
        ).aggregate(Sum("amount"))["amount__sum"] or Decimal("0")

        # Check if the spending has exceeded any thresholds
        total_spent_percentage = (total_spent / budget.amount) * 100

        # Check for warning and critical thresholds
        if total_spent_percentage >= budget.CRITICAL_THRESHOLD:
            send_budget_alert(budget, total_spent, critical=True)
        elif total_spent_percentage >= budget.WARNING_THRESHOLD:
            send_budget_alert(
                budget,
                total_spent,
            )
        budget.save()
    except Budget.DoesNotExist:
        pass


def send_budget_alert(budget, total_spent, critical=False):
    """Send an email notification if the budget limit is reached or exceeded."""
    percentage = (total_spent / budget.amount) * 100

    # Define the subject line based on the severity level
    if critical:
        subject = f"⚠️ CRITICAL: Budget Limit Exceeded for {budget.category.name}"
    else:
        subject = f"⚠️ Warning: Budget Usage High for {budget.category.name}"

    print(budget.amount)
    print(total_spent)
    # Prepare dynamic template data
    dynamic_template_data = {
        "subject": subject,
        "user_name": budget.user.name,
        "total_spent": f"{total_spent:,.2f}",
        "budget_amount": f"{budget.amount:,.2f}",
        "category_name": budget.category.name,
        "percentage": f"{percentage:.1f}",
    }

    # Send the email using SendGrid
    send_mail(
        user_email=budget.user.email,
        subject=subject,
        dynamic_template_data=dynamic_template_data,
        dynamic_template_id=settings.SENDGRID_BUDGET_TEMPLATE_ID,
    )
