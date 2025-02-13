from rest_framework import serializers
from decimal import Decimal
from saving_plan.models import SavingsTransaction
from user.models import CustomUser
from utils.is_uuid import is_uuid
from django.db import transaction


class SavingsTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavingsTransaction
        fields = [
            "id",
            "savings_plan",
            "amount",
            "date",
            "notes",
            "user",
        ]
        read_only_fields = ["date"]

    def validate_user(self, data):
        request = self.context["request"]
        user = request.user
        if user.is_staff and data.is_staff:
            raise serializers.ValidationError(
                "Staff users cannot create transactions for other staff"
            )
        if not user.is_staff and data != user:
            raise serializers.ValidationError(
                "You can only create transactions for yourself."
            )
        return data

    def validate_savings_plan(self, data):

        user = self.initial_data.get("user")
        saving_user = data.user
        if is_uuid(user):
            try:
                user_instance = CustomUser.objects.filter(id=user).first()
            except CustomUser.DoesNotExist:
                raise serializers.ValidationError("User does not exist.")

        if user_instance != saving_user:
            raise serializers.ValidationError(
                "You can only extend your own savings plans"
            )

        return data

    def validate_amount(self, value):
        """Validate the amount field."""
        if value is None:
            raise serializers.ValidationError("Amount is required")

        try:
            value = Decimal(str(value))
            if value <= 0:
                raise serializers.ValidationError(
                    "Contribution amount must be greater than 0"
                )
            return value
        except (TypeError, ValueError):
            raise serializers.ValidationError("Invalid amount format")

    def validate_notes(self, value):
        """Validate the notes field."""
        if value and len(value) > 500:  # Assuming max length is 500
            raise serializers.ValidationError("Notes cannot exceed 500 characters")
        return value

    def validate(self, data):
        """Perform object-level validation."""
        savings_plan = data.get(
            "savings_plan", getattr(self.instance, "savings_plan", None)
        )
        new_amount = data.get("amount", getattr(self.instance, "amount", None))

        if savings_plan and new_amount:
            current_total = savings_plan.get_total_saved()

            # If updating, subtract the old amount first
            if self.instance:
                new_total = current_total - self.instance.amount + new_amount
            else:
                new_total = current_total + new_amount

            if new_total > savings_plan.target_amount:
                raise serializers.ValidationError(
                    {"amount": "This contribution would exceed the target amount"}
                )

            # Store the new total for use in create/update
            self.new_total = new_total

        return data

    @transaction.atomic
    def create(self, validated_data):
        savings_plan = validated_data["savings_plan"]
        user = self.initial_data["user"]
        amount = validated_data["amount"]
        notes = validated_data.get("notes", "")

        # Create the transaction
        transaction = SavingsTransaction.objects.create(
            savings_plan=savings_plan,
            user_id=user,
            amount=amount,
            notes=notes,
        )

        # Update savings plan completion status if needed
        if hasattr(self, "new_total"):
            percentage = self.new_total / savings_plan.target_amount * 100
            if percentage >= 100 and not savings_plan.is_completed:
                savings_plan.is_completed = True
                savings_plan.save(update_fields=["is_completed"])

        return transaction

    @transaction.atomic
    def update(self, instance, validated_data):
        """Update the transaction and recalculate completion status."""

        old_amount = instance.amount  # Store old amount for calculation
        instance.amount = validated_data.get("amount", instance.amount)
        instance.notes = validated_data.get("notes", instance.notes)
        instance.save(update_fields=["amount", "notes"])

        # Recalculate total savings
        savings_plan = instance.savings_plan
        new_total = savings_plan.get_total_saved()

        # Update is_completed status correctly
        if new_total >= savings_plan.target_amount and not savings_plan.is_completed:
            savings_plan.is_completed = True
            savings_plan.save(update_fields=["is_completed"])
        elif new_total < savings_plan.target_amount and savings_plan.is_completed:
            savings_plan.is_completed = False
            savings_plan.save(update_fields=["is_completed"])

        return instance
