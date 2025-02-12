from celery import shared_task
from django.utils import timezone
from django.db import transaction
from services.notification import send_mail
from django.conf import settings
from transaction.models import Transaction
from .models import RecurringTransaction


@shared_task
def send_transaction_notification(
    user_name, user_email, amount, type_name, category_name, next_run_date
):
    """
    Asynchronously send email notification to user about the recurring transaction using SendGrid.
    """
    type_name = type_name.upper()

    # Define the subject line
    subject = f"Recurring {type_name} Transaction Processed"

    # Prepare dynamic template data
    dynamic_template_data = {
        "user_name": user_name,
        "amount": f"{amount}",
        "type_name": type_name,
        "category_name": category_name,
        "transaction_date": timezone.now().strftime("%B %d, %Y"),
        "next_run_date": next_run_date,
    }

    try:
        # Send the email using SendGrid
        send_mail(
            user_email=user_email,
            subject=subject,
            dynamic_template_data=dynamic_template_data,
            dynamic_template_id=settings.SENDGRID_RECURRING_TRANSACTION_TEMPLATE_ID,
        )
    except Exception as e:
        print(f"Failed to send email notification: {str(e)}")


@shared_task
def process_recurring_transactions():
    """Process all due recurring transactions"""
    now = timezone.now()

    # Get all non-deleted recurring transactions that are due
    recurring_transactions = RecurringTransaction.objects.filter(
        next_run__lte=now, is_deleted=False
    )

    for rec_txn in recurring_transactions:
        with transaction.atomic():
            # Check if related objects are deleted or if end_date has passed
            if (
                not rec_txn.user.is_active
                or rec_txn.category.is_deleted
                or (rec_txn.end_date and rec_txn.end_date < rec_txn.next_run)
            ):
                # Soft delete the recurring transaction
                rec_txn.is_deleted = True
                rec_txn.save()
                continue

            # Create the actual transaction
            Transaction.objects.create(
                user=rec_txn.user,
                category=rec_txn.category,
                type=rec_txn.type,
                amount=rec_txn.amount,
                date=rec_txn.next_run,
                description=rec_txn.description,
            )

            rec_txn.next_run = rec_txn.get_next_run_date(rec_txn.next_run)
            rec_txn.save()

            # Send email notification asynchronously
            send_transaction_notification.delay(
                user_name=rec_txn.user.name,
                user_email=rec_txn.user.email,
                amount=str(rec_txn.amount),
                type_name=rec_txn.type,
                category_name=rec_txn.category.name,
                next_run_date=rec_txn.next_run.strftime("%Y-%m-%d"),
            )
