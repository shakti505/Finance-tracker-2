from celery import shared_task
from services.notification import send_mail
from django.conf import settings
from django.db import transaction


@shared_task
def send_email_task(to_email, reset_link):
    """
    Send an email to the user with the password reset link.
    """
    subject = "Password Reset Request"
    dynamic_template_data = {
        "reset_link": reset_link,
    }
    send_mail(
        to_email,
        subject=subject,
        dynamic_template_data=dynamic_template_data,
        dynamic_template_id=settings.SENDGRID_RESET_PASSWORD_TEMPLATE_ID,
    )
    return "Email sent successfully"


@shared_task
def soft_delete_related_data(user):
    """
    Soft delete related data by setting is_deleted = True.
    """
    from transaction.models import Transaction
    from budget.models import Budget
    from category.models import Category
    from saving_plan.models import SavingsPlan, DeadlineExtension, SavingsTransaction
    from recurring_transaction.models import RecurringTransaction

    # Update all related records to is_deleted=True
    try:
        with transaction.atomic():
            Transaction.objects.filter(user=user).update(is_deleted=True)
            Budget.objects.filter(user=user).update(is_deleted=True)
            Category.objects.filter(user=user).update(is_deleted=True)
            SavingsPlan.objects.filter(user=user).update(is_deleted=True)
            SavingsTransaction.objects.filter(user=user).update(is_deleted=True)
            DeadlineExtension.objects.filter(user=user).update(is_deleted=True)
            RecurringTransaction.objects.filter(user=user).update(is_deleted=True)
        return "Related data soft deleted successfully."

    except Exception as e:
        return f"Error soft deleting related data: {str(e)}"
