# core/constants.py

class SavingsPlanStatus:
    """Enum for Savings Plan Status"""
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"

    CHOICES = [
        (ACTIVE, "Active"),
        (PAUSED, "Paused"),
        (COMPLETED, "Completed"),
    ]




class Frequency:
    """Enum for Savings Plan Contribution Frequency"""
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"

    CHOICES = [
        (DAILY, "Daily"),
        (WEEKLY, "Weekly"),
        (MONTHLY, "Monthly"),
    ]


class TransactionType:
    """Enum for Transaction Type"""
    CREDIT = "CREDIT"
    DEBIT = "DEBIT"

    CHOICES = [
        (CREDIT, "Credit"),
        (DEBIT, "Debit"),
    ]
