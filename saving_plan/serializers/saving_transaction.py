from rest_framework import serializers
from decimal import Decimal
from saving_plan.models import SavingsTransaction
from user.models import CustomUser
from utils.is_uuid import is_uuid


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
        print(user_instance)
        print(saving_user)
        if user_instance != saving_user:
            raise serializers.ValidationError(
                "You can only extend your own savings plans"
            )

        if data.status == "COMPLETED":
            raise serializers.ValidationError(
                "Cannot add transactions to completed savings plan"
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
        if "savings_plan" in data and "amount" in data:
            # Check if contribution would exceed target amount
            savings_plan = data["savings_plan"]
            new_amount = data["amount"]
            current_total = savings_plan.get_total_saved()

            if current_total + new_amount > savings_plan.target_amount:
                raise serializers.ValidationError(
                    {"amount": "This contribution would exceed the target amount"}
                )

        return data

    def create(self, validated_data):
        savings_plan = validated_data["savings_plan"]
        user = self.initial_data["user"]
        amount = validated_data["amount"]
        notes = validated_data.get("notes", "")
        transaction = SavingsTransaction.objects.create(
            savings_plan=savings_plan,
            user_id=user,
            amount=amount,
            notes=notes,
        )
        return transaction

    def update(self, instance, validated_data):
        """Update the transaction and recalculate the total saved amount."""
        instance.amount = validated_data.get("amount", instance.amount)
        instance.notes = validated_data.get("notes", instance.notes)
        instance.save(update_fields=["amount", "notes"])
        return instance
