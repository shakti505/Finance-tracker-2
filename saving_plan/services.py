# from django.db import transaction
# from django.core.exceptions import ValidationError
# from django.utils import timezone
# from decimal import Decimal


# class SavingsPlanService:
#     @staticmethod
#     def update_plan_status(plan):
#         """Updates the status of a savings plan based on current progress and deadline."""
#         today = timezone.now().date()
#         total_saved = plan.get_total_saved()

#         if total_saved >= plan.target_amount:
#             new_status = "COMPLETED"
#         elif today > plan.current_deadline and plan.extension_count >= 3:
#             new_status = "FAILED"
#         elif today > plan.current_deadline:
#             new_status = "EXTENDED"
#         else:
#             new_status = "ACTIVE"

#         if new_status != plan.status:
#             plan.status = new_status
#             plan.save(update_fields=["status", "updated_at"])

#     @staticmethod
#     @transaction.atomic
#     def extend_deadline(plan, new_deadline, user, reason=""):
#         """Extends the deadline of a savings plan with validation."""
#         MAX_EXTENSIONS = 3
#         MAX_EXTENSION_DAYS = 90

#         if not plan.can_extend_deadline():
#             raise ValidationError("Plan cannot be extended")

#         if plan.current_deadline >= new_deadline:
#             raise ValidationError("New deadline must be after current deadline")

#         extension_days = (new_deadline - plan.current_deadline).days
#         if extension_days <= 0 or extension_days > MAX_EXTENSION_DAYS:
#             raise ValidationError(
#                 f"Extension must be between 1 and {MAX_EXTENSION_DAYS} days"
#             )

#         DeadlineExtension.objects.create(
#             savings_plan=plan,
#             previous_deadline=plan.current_deadline,
#             new_deadline=new_deadline,
#             reason=reason,
#             extended_by=user,
#         )

#         plan.current_deadline = new_deadline
#         plan.extension_count += 1
#         plan.status = "EXTENDED"
#         plan.save(
#             update_fields=[
#                 "current_deadline",
#                 "extension_count",
#                 "status",
#                 "updated_at",
#             ]
#         )

#     @staticmethod
#     @transaction.atomic
#     def create_transaction(savings_plan, user, amount, notes=""):
#         """Creates a new savings transaction with validation."""
#         if savings_plan.status == "COMPLETED":
#             raise ValidationError("Cannot add transactions to completed savings plan")

#         if amount <= 0:
#             raise ValidationError("Contribution amount must be greater than 0")

#         current_total = savings_plan.get_total_saved()
#         if current_total + Decimal(str(amount)) > savings_plan.target_amount:
#             raise ValidationError("This contribution would exceed the target amount")

#         transaction = SavingsTransaction.objects.create(
#             savings_plan=savings_plan, user=user, amount_contributed=amount, notes=notes
#         )

#         SavingsPlanService.update_plan_status(savings_plan)
#         return transaction
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from django.db.models import Sum
from .models import SavingsTransaction, SavingsPlan, DeadlineExtension
from user.models import CustomUser


class SavingsPlanService:
    @staticmethod
    def update_plan_status(plan):
        """Updates the status of a savings plan based on current progress and deadline."""
        today = timezone.now().date()
        total_saved = plan.get_total_saved()

        if total_saved >= plan.target_amount:
            new_status = "COMPLETED"
        elif today > plan.current_deadline and plan.extension_count >= 3:
            new_status = "FAILED"
        elif today > plan.current_deadline:
            new_status = "EXTENDED"
        else:
            new_status = "ACTIVE"

        if new_status != plan.status:
            plan.status = new_status
            plan.save(update_fields=["status", "updated_at"])

    @staticmethod
    @transaction.atomic
    def extend_deadline(plan, new_deadline, user, reason=""):
        """Extends the deadline of a savings plan with validation."""
        MAX_EXTENSIONS = 3
        MAX_EXTENSION_DAYS = 90

        if not plan.can_extend_deadline():
            raise ValidationError("Plan cannot be extended")

        if plan.current_deadline >= new_deadline:
            raise ValidationError("New deadline must be after current deadline")

        extension_days = (new_deadline - plan.current_deadline).days
        if extension_days <= 0 or extension_days > MAX_EXTENSION_DAYS:
            raise ValidationError(
                f"Extension must be between 1 and {MAX_EXTENSION_DAYS} days"
            )

        DeadlineExtension.objects.create(
            savings_plan=plan,
            previous_deadline=plan.current_deadline,
            new_deadline=new_deadline,
            reason=reason,
            extended_by=user,
        )

        plan.current_deadline = new_deadline
        plan.extension_count += 1
        plan.status = "EXTENDED"
        plan.save(
            update_fields=[
                "current_deadline",
                "extension_count",
                "status",
                "updated_at",
            ]
        )

    @staticmethod
    @transaction.atomic
    def create_transaction(savings_plan, user, amount, notes=""):
        """Creates a new savings transaction with validation."""
        if savings_plan.status == "COMPLETED":
            raise ValidationError("Cannot add transactions to completed savings plan")

        if amount <= 0:
            raise ValidationError("Contribution amount must be greater than 0")

        current_total = savings_plan.get_total_saved()
        if current_total + Decimal(str(amount)) > savings_plan.target_amount:
            raise ValidationError("This contribution would exceed the target amount")

        transaction = SavingsTransaction.objects.create(
            savings_plan=savings_plan, user=user, amount_contributed=amount, notes=notes
        )

        SavingsPlanService.update_plan_status(savings_plan)
        return transaction
