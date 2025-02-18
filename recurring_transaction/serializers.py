from rest_framework import serializers
from django.utils import timezone
from django.db import transaction
from decimal import Decimal
from datetime import datetime
from utils.is_uuid import is_uuid
from user.models import CustomUser
from .models import RecurringTransaction


class RecurringTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecurringTransaction
        fields = [
            "id",
            "user",
            "category",
            "savings_plan",
            "type",
            "amount",
            "frequency",
            "start_date",
            "end_date",
            "next_run",
            "description",
        ]
        read_only_fields = ["id", "next_run"]

    def __init__(self, *args, **kwargs):
        """Ensure user field is ignored silently if present for normal users."""
        super().__init__(*args, **kwargs)
        request = self.context.get("request", None)

        if request and request.method in ["PATCH"]:
            self.fields["user"].read_only = True
            self.fields["type"].read_only = True
            self.fields["savings_plan"].read_only = True

    def _get_recurring_transaction_user(self):
        """Helper method to get and validate the recurring transaction user"""
        if self.instance:
            return self.instance.user
        if "user" not in self.initial_data:
            return None
        user_id = self.initial_data.get("user")
        if not is_uuid(user_id):
            return None
        user = CustomUser.objects.filter(id=user_id, is_active=True).first()
        return user

    def _get_recurring_transaction_type(self):
        """Helper method to get recurring transaction type"""
        if self.instance:
            return self.instance.type
        type = self.initial_data.get("type")
        return type

    def validate_user(self, user):
        """Validate user field with comprehensive checks"""
        request_user = self.context["request"].user

        if not user.is_active:
            raise serializers.ValidationError("User not found")

        if not request_user.is_staff and user != request_user:
            raise serializers.ValidationError(
                "You can only create recurring transactions for yourself."
            )
        if request_user.is_staff and user.is_staff:
            raise serializers.ValidationError(
                "Staff can only create recurring transactions for non-staff users."
            )
        return user
    def validate_type(self, type):
        savings_plan = self.initial_data.get("savings_plan")
        if savings_plan and type!= "DEBIT":
            raise serializers.ValidationError("You can not add ")
        return type
    def validate_amount(self, amount):
        """Validate transaction amount"""
        if amount <= 0:
            raise serializers.ValidationError("Amount must be a positive value.")
        return amount

    def validate_category(self, category):
        """Comprehensive category validation"""
        user = self._get_recurring_transaction_user()
        transaction_type = self._get_recurring_transaction_type()

        if not category.is_predefined and category.user != user:
            raise serializers.ValidationError(
                "Category does not belong to the provided user."
            )

        if category.type != transaction_type:
            raise serializers.ValidationError(
                "Category type must match the transaction type."
            )

        return category

    def validate_start_date(self, start_date):
        """Validate start date"""
        today = datetime.today().date()
        if start_date.date() < today:
            raise serializers.ValidationError("Start date cannot be in the past.")
        return start_date

    def validate(self, data):
        """Cross-field validations"""
        instance = self.instance
        category = data.get("category")
        savings_plan = data.get('savings_plan')
    
        if category and savings_plan:
            raise serializers.ValidationError(
                "A transaction can only be associated with either a category or a savings plan, not both."
            )

        if not category and not savings_plan:
            raise serializers.ValidationError(
                "A transaction must be associated with either a category or a savings plan."
            )
        # Validate end_date must be after start_date
        if "end_date" in data:
            start_date = data.get(
                "start_date", instance.start_date if instance else None
            )
            if data["end_date"].date() <= start_date.date():
                raise serializers.ValidationError(
                    {"End_date": "End date must be after start date."}
                )
        return data
    
    def validate_savings_plan(self, savings_plan):
        """Ensure savings plan belongs to the user and is not completed or paused"""
        user = self._get_recurring_transaction_user()

        if not savings_plan:
            raise serializers.ValidationError("Savings plan is required.")

        if savings_plan.user != user:
            raise serializers.ValidationError("Savings plan does not belong to the provided user.")

        if savings_plan.is_deleted:
            raise serializers.ValidationError("Savings plan not found.")

        if savings_plan.status in ["COMPLETED", "PAUSED"]:
            raise serializers.ValidationError(f"Cannot add transactions to a {savings_plan.status.lower()} savings plan.")

        transaction_amount = self.initial_data.get("amount")

        if transaction_amount:
            try:
                transaction_amount = Decimal(transaction_amount)
            except (ValueError, TypeError):
                raise serializers.ValidationError("Invalid transaction amount.")

            remaining_amount = savings_plan.get_remaining_amount()

            if transaction_amount > remaining_amount:
                raise serializers.ValidationError(
                    f"Transaction exceeds the remaining savings target by {transaction_amount - remaining_amount}."
                )

        return savings_plan


    @transaction.atomic
    def create(self, validated_data):
        """Create a recurring transaction and update savings plan status if necessary."""
        validated_data["next_run"] = validated_data["start_date"]
        instance = super().create(validated_data)

        return instance


    @transaction.atomic
    def update(self, instance, validated_data):
        """Update a recurring transaction and check if savings plan status needs to be changed."""

        validated_data["next_run"] = validated_data.get("start_date", instance.next_run)

        instance = super().update(instance, validated_data)
        return instance
