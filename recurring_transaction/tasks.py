# from celery import shared_task
# from django.utils import timezone
# from django.db import transaction
# from django.conf import settings
# from services.notification import send_mail
# from transaction.models import Transaction
# from .models import RecurringTransaction
# from transaction.tasks import track_and_notify_budget


# @shared_task
# def send_transaction_notification(
#     user_name,
#     user_email,
#     amount,
#     type_name,
#     category_name,
#     next_run_date,
#     transaction_date,
# ):
#     """
#     Asynchronously send email notification to user about the recurring transaction using SendGrid.
#     """
#     subject = f"Recurring {type_name.upper()} Transaction Processed"

#     dynamic_template_data = {
#         "user_name": user_name,
#         "amount": str(amount),
#         "type_name": type_name.upper(),
#         "category_name": category_name,
#         "transaction_date": transaction_date,
#         "next_run_date": next_run_date,
#     }

#     try:
#         send_mail(
#             user_email=user_email,
#             subject=subject,
#             dynamic_template_data=dynamic_template_data,
#             dynamic_template_id=settings.SENDGRID_RECURRING_TRANSACTION_TEMPLATE_ID,
#         )
#     except Exception as e:
#         print(f"Failed to send email notification: {str(e)}")


# @shared_task
# def process_recurring_transactions():
#     """Process all due recurring transactions."""
#     now = timezone.now()

#     recurring_transactions = RecurringTransaction.objects.filter(
#         next_run__lte=now, is_deleted=False
#     )

#     for rec_txn in recurring_transactions:
#         with transaction.atomic():
#             if (
#                 not rec_txn.user.is_active
#                 or rec_txn.category.is_deleted
#                 or (rec_txn.end_date and rec_txn.end_date < rec_txn.next_run)
#             ):
#                 rec_txn.is_deleted = True
#                 rec_txn.save()
#                 continue

#             transaction = Transaction.objects.create(
#                 user=rec_txn.user,
#                 category=rec_txn.category,
#                 type=rec_txn.type,
#                 amount=rec_txn.amount,
#                 date=rec_txn.next_run,
#                 description=rec_txn.description,
#             )
#             track_and_notify_budget.delay(transaction.id)
#             rec_txn.next_run = rec_txn.get_next_run_date(rec_txn.next_run)
#             rec_txn.save()

#             send_transaction_notification.delay(
#                 user_name=rec_txn.user.name,
#                 user_email=rec_txn.user.email,
#                 amount=rec_txn.amount,
#                 type_name=rec_txn.type,
#                 category_name=rec_txn.category.name,
#                 next_run_date=rec_txn.next_run.strftime("%Y-%m-%d"),
#                 transaction_date=transaction.date.strftime("%Y-%m-%d %H:%M:%S"),
#             )

# from celery import shared_task
# from django.utils import timezone
# from django.db import transaction
# from django.conf import settings
# from decimal import Decimal
# from django.db.models import Sum
# from services.notification import send_mail
# from transaction.models import Transaction
# from .models import RecurringTransaction
# from saving_plan.models import SavingsPlan
# from transaction.tasks import track_and_notify_budget


# @shared_task
# def send_transaction_notification(
#     user_name,
#     user_email,
#     amount,
#     type_name,
#     category_name,
#     savings_plan_name,
#     next_run_date,
#     transaction_date,
# ):
#     """
#     Asynchronously send email notification to user about the recurring transaction using SendGrid.
#     """
#     subject = f"Recurring {type_name.upper()} Transaction Processed"

#     dynamic_template_data = {
#         "user_name": user_name,
#         "amount": str(amount),
#         "type_name": type_name.upper(),
#         "category_name": category_name if category_name else "N/A",
#         "savings_plan_name": savings_plan_name if savings_plan_name else "N/A",
#         "transaction_date": transaction_date,
#         "next_run_date": next_run_date,
#     }

#     try:
#         send_mail(
#             user_email=user_email,
#             subject=subject,
#             dynamic_template_data=dynamic_template_data,
#             dynamic_template_id=settings.SENDGRID_RECURRING_TRANSACTION_TEMPLATE_ID,
#         )
#     except Exception as e:
#         print(f"Failed to send email notification: {str(e)}")


# @shared_task
# def process_recurring_transactions():
#     """Process all due recurring transactions."""
#     now = timezone.now()

#     recurring_transactions = RecurringTransaction.objects.filter(
#         next_run__lte=now, is_deleted=False
#     )

#     for rec_txn in recurring_transactions:
#         with transaction.atomic():
#             # Skip transactions if the user is inactive or the transaction has ended
#             if (
#                 not rec_txn.user.is_active
#                 or (rec_txn.category and rec_txn.category.is_deleted)
#                 or (rec_txn.savings_plan and rec_txn.savings_plan.is_deleted)
#                 or (rec_txn.end_date and rec_txn.end_date < rec_txn.next_run)
#             ):
#                 rec_txn.is_deleted = True
#                 rec_txn.save(update_fields=["is_deleted"])
#                 continue

#             # Determine whether it's a category or savings plan transaction
#             category_name = rec_txn.category.name if rec_txn.category else None
#             savings_plan_name = rec_txn.savings_plan.name if rec_txn.savings_plan else None

#             # Create transaction
#             transaction = Transaction.objects.create(
#                 user=rec_txn.user,
#                 category=rec_txn.category if rec_txn.category else None,
#                 savings_plan=rec_txn.savings_plan if rec_txn.savings_plan else None,
#                 type=rec_txn.type,
#                 amount=rec_txn.amount,
#                 date=rec_txn.next_run,
#                 description=rec_txn.description,
#             )

#             # If it's a category transaction, track the budget
#             if rec_txn.category:
#                 track_and_notify_budget.delay(transaction.id)

#             # If it's a savings plan transaction, check if it hits the target
#             if rec_txn.savings_plan:
#                 savings_plan = rec_txn.savings_plan
#                 total_saved = Transaction.objects.filter(
#                     savings_plan=savings_plan, is_deleted=False
#                 ).aggregate(total=Sum('amount'))['total'] or Decimal("0")

#                 if total_saved >= savings_plan.target_amount and savings_plan.status != "COMPLETED":
#                     savings_plan.status = "COMPLETED"
#                     savings_plan.save(update_fields=["status"])
                    
#                     # Send email notification when the savings plan is completed
#                     send_mail(
#                         user_email=rec_txn.user.email,
#                         subject=f"🎉 Savings Plan '{savings_plan.name}' Completed!",
#                         dynamic_template_data={
#                             "user_name": rec_txn.user.name,
#                             "savings_plan_name": savings_plan.name,
#                             "total_saved": f"{total_saved:,.2f}",
#                             "target_amount": f"{savings_plan.target_amount:,.2f}",
#                             "message": f"Your savings plan '{savings_plan.name}' has been successfully completed!",
#                         },
#                         dynamic_template_id=settings.SENDGRID_SAVINGS_PLAN_COMPLETION_TEMPLATE_ID,
#                     )

#             # Update next_run
#             rec_txn.next_run = rec_txn.get_next_run_date(rec_txn.next_run)
#             rec_txn.save(update_fields=["next_run"])

#             # Send notification email
#             send_transaction_notification.delay(
#                 user_name=rec_txn.user.name,
#                 user_email=rec_txn.user.email,
#                 amount=rec_txn.amount,
#                 type_name=rec_txn.type,
#                 category_name=category_name,
#                 savings_plan_name=savings_plan_name,
#                 next_run_date=rec_txn.next_run.strftime("%Y-%m-%d"),
#                 transaction_date=transaction.date.strftime("%Y-%m-%d %H:%M:%S"),
#             )

from celery import shared_task, Task
from django.utils import timezone
from django.db import transaction
from django.conf import settings
from decimal import Decimal
from django.db.models import Sum, F
from services.notification import send_mail
from django.core.cache import cache
from typing import Optional, Dict, Any
from utils.logging import logger
from transaction.models import Transaction
from .models import RecurringTransaction
from transaction.tasks import track_and_notify_budget

class TransactionNotificationTask(Task):
    max_retries = 3
    default_retry_delay = 60  # 1 minute

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(f"Transaction notification failed: {exc}", exc_info=True)
        super().on_failure(exc, task_id, args, kwargs, einfo)

@shared_task(base=TransactionNotificationTask)
def send_transaction_notification(
    user_name: str,
    user_email: str,
    dynamic_template_data: Dict[str, Any],
    dynamic_template_id: str
) -> None:
    """Send transaction email notification with retry logic"""
    try:
        send_mail(
            user_email=user_email,
            subject=dynamic_template_data.get("subject", "Recurring Transaction"),
            dynamic_template_data=dynamic_template_data,
            dynamic_template_id=dynamic_template_id,
        )
    except Exception as e:
        logger.error(f"Email notification failed: {str(e)}", exc_info=True)
        raise send_transaction_notification.retry(exc=e)

class SavingsPlanManager:
    @staticmethod
    def update_status(plan, total_saved: Decimal) -> None:
        """Update savings plan status and notify user if completed"""
        if total_saved >= plan.target_amount and plan.status != "COMPLETED":
            plan.status = "COMPLETED"
            plan.save(update_fields=["status"])
            
            # Send completion notification
            notification_data = {
                "user_name": plan.user.name,
                "savings_plan_name": plan.name,
                "total_saved": f"{total_saved:,.2f}",
                "target_amount": f"{plan.target_amount:,.2f}",
                "message": f"Congratulations! Your savings plan '{plan.name}' has been completed!"
            }
            
            send_transaction_notification.delay(
                plan.user.name,
                plan.user.email,
                notification_data,
                settings.SENDGRID_SAVINGS_PLAN_COMPLETION_TEMPLATE_ID
            )

@shared_task
def process_recurring_transactions():
    """Process daily recurring transactions - Runs once per day"""
    
    # Prevent duplicate execution using cache lock
    if cache.get("processing_recurring_transactions"):
        return  # Skip execution if already running
    
    cache.set("processing_recurring_transactions", True, timeout=600)  # Lock for 10 minutes

    try:
        now = timezone.now()
        
        # Fetch transactions due today
        recurring_transactions = (
            RecurringTransaction.objects
            .select_related('user', 'category', 'savings_plan')
            .filter(next_run__lte=now, is_deleted=False)
            .iterator()
        )

        for rec_txn in recurring_transactions:
            cache_key = f"processing_rec_txn_{rec_txn.id}"
            
            # Prevent duplicate processing
            if cache.get(cache_key):
                continue

            try:
                cache.set(cache_key, True, timeout=300)  # Lock for 5 minutes
                
                with transaction.atomic():
                    if not _is_transaction_valid(rec_txn):
                        rec_txn.is_deleted = True
                        rec_txn.save(update_fields=["is_deleted"])
                        continue

                    # Create new transaction
                    new_transaction = _create_transaction(rec_txn)

                    # Handle category or savings plan
                    if rec_txn.category:
                        track_and_notify_budget.delay(new_transaction.id)
                    elif rec_txn.savings_plan:
                        _process_savings_plan(rec_txn, new_transaction)

                    # Update next run date
                    RecurringTransaction.objects.filter(id=rec_txn.id).update(
                        next_run=rec_txn.get_next_run_date(rec_txn.next_run)
                    )

                    # Send notification
                    send_transaction_notification.delay(
                        rec_txn.user.name, 
                        rec_txn.user.email, 
                        {
                            "subject": "Recurring Transaction",
                            "transaction_amount": f"{rec_txn.amount:.2f}",
                            "transaction_date": rec_txn.next_run.strftime("%Y-%m-%d"),
                            "description": rec_txn.description or "No description provided",
                        }, 
                        settings.SENDGRID_RECURRING_TRANSACTION_TEMPLATE_ID
                    )

            except Exception as e:
                logger.error(f"Error processing recurring transaction {rec_txn.id}: {str(e)}", exc_info=True)
            finally:
                cache.delete(cache_key)

    finally:
        cache.delete("processing_recurring_transactions")  # Release global lock

def _is_transaction_valid(rec_txn) -> bool:
    """Check if the recurring transaction is valid for processing"""
    return (
        rec_txn.user.is_active
        and not (rec_txn.category and rec_txn.category.is_deleted)
        and not (rec_txn.savings_plan and rec_txn.savings_plan.is_deleted)
        and not (rec_txn.end_date and rec_txn.end_date < rec_txn.next_run)
    )

def _create_transaction(rec_txn) -> Transaction:
    """Create a new transaction for the recurring transaction"""
    return Transaction.objects.create(
        user=rec_txn.user,
        category=rec_txn.category,
        savings_plan=rec_txn.savings_plan,
        type=rec_txn.type,
        amount=rec_txn.amount,
        date=rec_txn.next_run,
        description=rec_txn.description,
    )

def _process_savings_plan(rec_txn, transaction) -> None:
    """Process a savings plan transaction"""
    savings_plan = rec_txn.savings_plan
    cache_key = f"savings_plan_total_{savings_plan.id}"
    
    # Use cache to reduce DB queries
    total_saved = cache.get(cache_key)
    if total_saved is None:
        total_saved = Transaction.objects.filter(
            savings_plan=savings_plan,
            is_deleted=False
        ).aggregate(total=Sum('amount'))['total'] or Decimal("0")

    # Add new transaction amount to total saved
    total_saved += transaction.amount
    cache.set(cache_key, total_saved, timeout=3600)  # Cache for 1 hour

    # Check if the total saved amount now meets or exceeds the target
    if total_saved >= savings_plan.target_amount:
        savings_plan.status = "COMPLETED"
        savings_plan.save(update_fields=["status"])
        
        # Send completion notification
        notification_data = {
            "user_name": savings_plan.user.name,
            "savings_plan_name": savings_plan.name,
            "total_saved": f"{total_saved:,.2f}",
            "target_amount": f"{savings_plan.target_amount:,.2f}",
            "message": f"Congratulations! Your savings plan '{savings_plan.name}' has been completed!"
        }
        
        send_transaction_notification.delay(
            savings_plan.user.email,
            "Savings PLan Completed",
            notification_data,
            settings.SENDGRID_GOAL_COMPLETED_TEMPLATE_ID
        )

