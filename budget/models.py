from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from user.models import CustomUser
from category.models import Category
from utils.models import BaseModel
from datetime import timedelta


class Budget(BaseModel):
    """
    Budget model with threshold crossing detection and spam prevention.
    """

    WARNING_THRESHOLD = Decimal("90.00")
    CRITICAL_THRESHOLD = Decimal("100.00")

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="budgets",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="budgets",
    )
    year = models.PositiveIntegerField()
    month = models.PositiveIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(12),
        ]
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    class Meta:
        ordering = ["-year", "-month"]
        unique_together = ["user", "category", "year", "month", "is_deleted"]
