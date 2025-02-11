from django.db import models
from django.utils import timezone
from user.models import CustomUser
from category.models import Category
from utils.models import BaseModel
from dateutil.relativedelta import relativedelta
import calendar


class RecurringTransaction(BaseModel):
    """Model to store recurring transaction details with advanced scheduling"""

    FREQUENCY_CHOICES = [
        ("daily", "Daily"),
        ("weekly", "Weekly"),
        ("monthly", "Monthly"),
        ("yearly", "Yearly"),
    ]

    TYPE_CHOICES = [
        ("credit", "Credit"),
        ("debit", "Debit"),
    ]

    STATUS_CHOICES = [
        ("active", "Active"),
        ("paused", "Paused"),
        ("completed", "Completed"),
    ]

    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="recurring_transaction"
    )
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="recurring_transaction"
    )
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)
    next_run = models.DateTimeField()
    description = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="active")

    def save(self, *args, **kwargs):
        """Automatically set the next_run date when a new recurring transaction is created."""

        super().save(*args, **kwargs)

    def get_next_run_date(self, current_date):
        """
        Calculate the next run date with special handling for monthly transactions
        """
        if self.frequency == "daily":
            return current_date + timezone.timedelta(days=1)
        elif self.frequency == "weekly":
            return current_date + timezone.timedelta(weeks=1)
        elif self.frequency == "monthly":
            return self.calculate_monthly_next_run(current_date)
        elif self.frequency == "yearly":
            return self.calculate_yearly_next_run(current_date)
        return current_date

    def calculate_monthly_next_run(self, current_date):
        """Handle monthly transactions while preserving the original day of the month."""
        next_month = current_date + relativedelta(months=1)
        last_day_of_month = calendar.monthrange(next_month.year, next_month.month)[1]
        return next_month.replace(day=min(self.start_date.day, last_day_of_month))

    def calculate_yearly_next_run(self, current_date):
        """Handle yearly transactions while accounting for leap years."""
        next_year = current_date + relativedelta(years=1)
        if self.start_date.month == 2 and self.start_date.day == 29:
            if calendar.isleap(next_year.year):
                return next_year.replace(month=2, day=29)
            return next_year.replace(month=2, day=28)

    def __str__(self):
        return f"{self.user} - {self.type} - {self.amount} - {self.frequency}"
