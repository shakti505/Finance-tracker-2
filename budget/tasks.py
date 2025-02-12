from .models import Budget
from .utils import monitor_budget_and_notify
from celery import shared_task


@shared_task
def process_budget_spending(budget_id):
    """
    Calculate total transactions for a budget based on its date, category, and user
    """
    budget = Budget.objects.get(id=budget_id)
    monitor_budget_and_notify(budget)
