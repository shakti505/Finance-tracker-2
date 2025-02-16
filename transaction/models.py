import uuid
from django.db import models
from user.models import CustomUser
from category.models import Category
from utils.models import BaseModel
from saving_plan.models import SavingsPlan
from utils.constants import TransactionType
class Transaction(BaseModel):
    """Transaction Model (No Direct Budget Link)"""


    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="transactions"
    )
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="transactions", blank=True, null=True
    )
    savings_plan = models.ForeignKey(
        SavingsPlan, on_delete=models.CASCADE, related_name="transactions", blank=True, null=True
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField()
    description = models.TextField(blank=True)
    type = models.CharField(max_length=10, choices=TransactionType.CHOICES)
