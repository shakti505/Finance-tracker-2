from celery import shared_task, Task
from django.utils import timezone
from django.db import transaction
from django.conf import settings
from decimal import Decimal
from django.db.models import Sum
from services.notification import send_mail
from typing import  Dict, Any
from utils.logging import logger
from transaction.models import Transaction
from .models import RecurringTransaction
from transaction.tasks import track_and_notify_budget

class TransactionNotificationTask(Task):
    max_retries = 3
    default_retry_delay = 60

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(f"Transaction notification failed: {exc}", exc_info=True)
        super().on_failure(exc, task_id, args, kwargs, einfo)

@shared_task(base=TransactionNotificationTask)
def send_transaction_notification(
    user_email: str,
    subject:str,
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
                plan.user.email,
                "Reccuring Transaction Created",
                notification_data,
                settings.SENDGRID_SAVINGS_PLAN_COMPLETION_TEMPLATE_ID
            )

@shared_task
def process_recurring_transactions():
    """Process daily recurring transactions - Runs once per day"""
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
            try:
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
                        rec_txn.user.email, 
                        "",
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

    except Exception as e:
        logger.error(f"Error processing recurring transactions: {str(e)}", exc_info=True)

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
    total_saved = Transaction.objects.filter(
        savings_plan=savings_plan,
        is_deleted=False
    ).aggregate(total=Sum('amount'))['total'] or Decimal("0")

    # Add new transaction amount to total saved
    total_saved += transaction.amount

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
