from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from user.models import CustomUser
import uuid
from utils.models import BaseModel
from utils.constants import SavingsPlanStatus, Frequency


class SavingsPlan(BaseModel):
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="savings_plans"
    )
    name = models.CharField(
        max_length=100,
    )
    target_amount = models.DecimalField(max_digits=10, decimal_places=2)
    original_deadline = models.DateField()
    current_deadline = models.DateField()
    status = models.CharField(max_length=10, choices=SavingsPlanStatus.CHOICES, default=SavingsPlanStatus.ACTIVE)
    frequency = models.CharField(max_length=10, choices=Frequency.CHOICES)

    def get_total_saved(self):
        return (
            self.transactions.filter(is_deleted=False).aggregate(
                total=models.Sum("amount")
            )["total"]
            or 0
        )

    def get_remaining_amount(self):
        return self.target_amount - self.get_total_saved()

    def is_overdue(self):
        return timezone.now().date() > self.current_deadline

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                check=models.Q(target_amount__gt=0), name="positive_target_amount"
            )
        ]



