from celery import shared_task
from budget.models import Budget
from transaction.models import Transaction
from budget.utils import monitor_budget_and_notify


from django.core.exceptions import ObjectDoesNotExist

@shared_task
def track_and_notify_budget(transaction_id):
    try:
        transaction = Transaction.objects.select_related("user", "category").filter(id=transaction_id).first()
        
        if not transaction:
            raise ObjectDoesNotExist(f"Transaction with ID {transaction_id} does not exist.")


    except ObjectDoesNotExist as e:
        print(f"Error: {e}")
