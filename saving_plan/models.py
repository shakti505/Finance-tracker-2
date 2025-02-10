from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from user.models import CustomUser
import uuid
from utils.models import BaseModel


class SavingsPlan(BaseModel):
    PRIORITY_CHOICES = [("HIGH", "High"), ("MEDIUM", "Medium"), ("LOW", "Low")]
    FREQUENCY_CHOICES = [
        ("DAILY", "Daily"),
        ("WEEKLY", "Weekly"),
        ("MONTHLY", "Monthly"),
    ]
    STATUS_CHOICES = [
        ("ACTIVE", "Active"),
        ("COMPLETED", "Completed"),
        ("EXTENDED", "Extended"),
        ("FAILED", "Failed"),
    ]

    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="savings_plans"
    )
    name = models.CharField(
        max_length=100,
    )
    target_amount = models.DecimalField(max_digits=10, decimal_places=2)
    original_deadline = models.DateField()
    current_deadline = models.DateField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES)
    frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="ACTIVE")

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


class SavingsTransaction(BaseModel):
    savings_plan = models.ForeignKey(
        SavingsPlan, on_delete=models.CASCADE, related_name="transactions"
    )
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="savings_transactions"
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateTimeField(auto_now_add=True)

    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-date"]


class DeadlineExtension(BaseModel):

    savings_plan = models.ForeignKey(
        SavingsPlan, on_delete=models.CASCADE, related_name="deadline_extensions"
    )
    previous_deadline = models.DateField()
    new_deadline = models.DateField()
    reason = models.TextField(blank=True)
    extended_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="deadline_extensions"
    )

    class Meta:
        ordering = ["-extended_at"]
