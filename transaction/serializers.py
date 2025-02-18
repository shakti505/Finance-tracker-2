# from rest_framework import serializers
# from .models import Transaction
# from utils.is_uuid import is_uuid
# from user.models import CustomUser


# class TransactionSerializer(serializers.ModelSerializer):
#     """Serializer for Transaction model."""

#     class Meta:
#         model = Transaction
#         fields = [
#             "id",
#             "type",
#             "amount",
#             "category",
#             "user",
#             "date",
#             "description",
#             "created_at",
#             "updated_at",
#             "is_deleted",
#         ]
#         read_only_fields = ["id", "created_at", "updated_at", "is_deleted"]

#     def __init__(self, *args, **kwargs):
#         """Ensure user and type fields are read-only for updates."""
#         super().__init__(*args, **kwargs)
#         request = self.context.get("request")
#         if request and request.method in ["PATCH"]:
#             self.fields["user"].read_only = True
#             self.fields["type"].read_only = True

#     def _get_transaction_user(self):
#         """Helper method to get and validate the transaction user."""
#         if self.instance:
#             return self.instance.user

#         if "user" not in self.initial_data:
#             return None

#         user_id = self.initial_data.get("user")

#         if not is_uuid(user_id):
#             return None

#         user = CustomUser.objects.filter(id=user_id, is_active=True).first()
#         return user

#     def _get_transaction_type(self):
#         """Helper method to get transaction type."""
#         if self.instance:
#             return self.instance.type
#         type = self.initial_data.get("type")
#         return type

#     def validate_amount(self, amount):
#         """Ensure amount is positive."""
#         if amount <= 0:
#             raise serializers.ValidationError("Amount must be a positive value.")
#         return amount

#     def validate_user(self, user):
#         """Ensure valid user selection based on user role."""
#         request_user = self.context["request"].user

#         if not user.is_active:
#             raise serializers.ValidationError("User not found.")

#         if not request_user.is_staff and user != request_user:
#             raise serializers.ValidationError(
#                 "You can only create transactions for yourself."
#             )
#         if request_user.is_staff and user.is_staff:
#             raise serializers.ValidationError(
#                 "Staff can only create transactions for non-staff users."
#             )
#         return user

#     def validate_category(self, category):
#         """Ensure category belongs to the user and matches transaction type."""

#         type = self._get_transaction_type()
#         user = self._get_transaction_user()
#         if not category.is_predefined and category.user != user:
#             raise serializers.ValidationError(
#                 "Category does not belong to the provided user."
#             )
#         if category.is_deleted:
#             raise serializers.ValidationError("Category not found.")
#         if category.type != type:
#             raise serializers.ValidationError(
#                 "Category type does not match transaction type."
#             )
#         return category


from rest_framework import serializers
from .models import Transaction
from utils.is_uuid import is_uuid
from user.models import CustomUser
from decimal import Decimal
from django.db import models
from saving_plan.tasks import send_savings_plan_completion_notification
from datetime import datetime


class TransactionSerializer(serializers.ModelSerializer):
    """Serializer for Transaction model with mutual exclusivity between category and savings_plan."""

    class Meta:
        model = Transaction
        fields = [
            "id",
            "type",
            "amount",
            "category",
            "savings_plan",
            "user",
            "date",
            "description",
            "created_at",
            "updated_at",
            "is_deleted",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "is_deleted"]

    def __init__(self, *args, **kwargs):
        """Ensure user and type fields are read-only for updates."""
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request and request.method in ["PATCH"]:
            self.fields["user"].read_only = True
            self.fields["type"].read_only = True

    def _get_transaction_user(self):
        """Helper method to get and validate the transaction user."""
        if self.instance:
            return self.instance.user

        if "user" not in self.initial_data:
            return None

        user_id = self.initial_data.get("user")

        if not is_uuid(user_id):
            return None

        user = CustomUser.objects.filter(id=user_id, is_active=True).first()
        return user

    def _get_transaction_type(self):
        """Helper method to get transaction type."""
        if self.instance:
            return self.instance.type
        type = self.initial_data.get("type")
        return type


    def validate(self, data):
        """
        Validate that transaction date does not exceed savings plan deadline.
        """
        category = data.get("category")
        savings_plan = data.get("savings_plan")
        transaction_date = data.get("date")
        if category and savings_plan:
            raise serializers.ValidationError(
            "A transaction can only be associated with either a category or a savings plan, not both."
        )

        if not category and not savings_plan:
            raise serializers.ValidationError(
            "A transaction must be associated with either a category or a savings plan."
        )

        if savings_plan and transaction_date:
            savings_plan_deadline = savings_plan.current_deadline

            # Convert datetime to date for comparison
            if isinstance(transaction_date, datetime):
                transaction_date = transaction_date.date()

            if transaction_date > savings_plan_deadline:
                raise serializers.ValidationError(
                    "Transaction date cannot be after the savings plan's deadline."
                )

        return data



    def validate_amount(self, amount):
        """Ensure amount is positive."""
        if amount <= 0:
            raise serializers.ValidationError("Amount must be a positive value.")
        return amount

    def validate_user(self, user):
        """Ensure valid user selection based on user role."""
        request_user = self.context["request"].user

        if not user.is_active:
            raise serializers.ValidationError("User not found.")

        if not request_user.is_staff and user != request_user:
            raise serializers.ValidationError(
                "You can only create transactions for yourself."
            )
        if request_user.is_staff and user.is_staff:
            raise serializers.ValidationError(
                "Staff can only create transactions for non-staff users."
            )
        return user

    def validate_category(self, category):
        """Ensure category belongs to the user and matches transaction type."""
        type = self._get_transaction_type()
        user = self._get_transaction_user()
        
        if not category.is_predefined and category.user != user:
            raise serializers.ValidationError(
                "Category does not belong to the provided user."
            )
        if category.is_deleted:
            raise serializers.ValidationError("Category not found.")
        if category.type != type:
            raise serializers.ValidationError(
                "Category type does not match transaction type."
            )
        return category

    def validate_savings_plan(self, savings_plan):
        """Ensure savings plan belongs to the user and is not completed or paused."""
        user = self._get_transaction_user()

        if savings_plan.user != user:
            raise serializers.ValidationError("Savings plan does not belong to the provided user.")

        if savings_plan.is_deleted:
            raise serializers.ValidationError("Savings plan not found.")

        if savings_plan.status == "COMPLETED":
            raise serializers.ValidationError("Cannot add transactions to a completed savings plan.")

        if savings_plan.status == "PAUSED":
            raise serializers.ValidationError("Cannot add transactions to a paused savings plan.")

        transaction_amount = self.initial_data.get("amount")
        if transaction_amount:
            try:
                transaction_amount = float(transaction_amount)
            except ValueError:
                raise serializers.ValidationError("Invalid transaction amount.")

            remaining_amount = savings_plan.get_remaining_amount()

            if transaction_amount > remaining_amount:
                raise serializers.ValidationError(
                    f"Transaction exceeds the remaining savings target by {Decimal(transaction_amount) - Decimal(remaining_amount)}.")

        return savings_plan
    def create(self, validated_data):
        """Create a transaction and update savings plan status if target is met."""
        transaction = super().create(validated_data)
        savings_plan = transaction.savings_plan

        if savings_plan:
            # Calculate total saved amount
            current_total = Transaction.objects.filter(
                savings_plan=savings_plan,
                is_deleted=False
            ).aggregate(total=models.Sum('amount'))['total'] or Decimal("0")

            # Update savings plan status based on total saved amount
            if current_total >= savings_plan.target_amount and savings_plan.status != "COMPLETED":
                savings_plan.status = "COMPLETED"
                savings_plan.save(update_fields=["status"])
                send_savings_plan_completion_notification.delay(savings_plan.id)

        return transaction



    def update(self, instance, validated_data):
        """Update a transaction and check savings plan status."""
        old_amount = instance.amount  # Store the old amount before update
        transaction = super().update(instance, validated_data)
        savings_plan = transaction.savings_plan

        if savings_plan:
            # Calculate total saved amount after update
            current_total = Transaction.objects.filter(
                savings_plan=savings_plan,
                is_deleted=False
            ).aggregate(total=models.Sum('amount'))['total'] or Decimal("0")

            # Update savings plan status based on new total saved amount
            if current_total >= savings_plan.target_amount and savings_plan.status != "COMPLETED":
                savings_plan.status = "COMPLETED"
                savings_plan.save(update_fields=["status"])
                send_savings_plan_completion_notification.delay(savings_plan.id)

            elif current_total < savings_plan.target_amount and savings_plan.status == "COMPLETED":
                savings_plan.status = "ACTIVE"
                savings_plan.save(update_fields=["status"])

        return transaction
