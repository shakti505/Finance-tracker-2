from celery import shared_task
from budget.models import Budget
from transaction.models import Transaction
from budget.utils import monitor_budget_and_notify


@shared_task
def track_and_notify_budget(transaction_id):
    """
    Asynchronously track the budget and send a notification if the limit is reached.
    """
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
    monitor_budget_and_notify(budget)
