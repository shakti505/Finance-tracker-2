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

    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="recurring_transactions"
    )

    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="recurring_transactions"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)
    next_run = models.DateTimeField()
    description = models.TextField(blank=True)

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
        """
        Handles monthly transactions while preserving the original day of the month when possible.
        Always tries to use the start_date day, falling back to the last day of the month
        if the original day doesn't exist in the target month.
        """
        # Calculate next month's date
        next_month = current_date + relativedelta(months=1)

        # Get the actual last day of the target month using calendar
        last_day_of_month = calendar.monthrange(next_month.year, next_month.month)[1]

        # If start_date.day is 31 and next month has fewer days, use the last day of that month
        target_day = min(self.start_date.day, last_day_of_month)

        result = next_month.replace(day=target_day)

        return result

    def calculate_yearly_next_run(self, current_date):
        """Handle yearly transactions with leap year logic"""
        next_year = current_date + relativedelta(years=1)

        if current_date.month == 2 and current_date.day == 29:
            try:
                next_year.replace(month=2, day=29)
            except ValueError:
                return next_year.replace(month=2, day=28)

        return next_year

    def __str__(self):
        return f"{self.user} - {self.type} - {self.amount} - {self.frequency}"
