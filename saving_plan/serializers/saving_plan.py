from rest_framework import serializers, status, permissions
from django.utils import timezone
from decimal import Decimal
from saving_plan.models import SavingsPlan, SavingsTransaction, DeadlineExtension
from user.models import CustomUser
from utils.is_uuid import is_uuid


class SavingsPlanSerializer(serializers.ModelSerializer):

    total_saved = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()
    time_remaining = serializers.SerializerMethodField()

    class Meta:
        model = SavingsPlan
        fields = [
            "id",
            "name",
            "target_amount",
            "original_deadline",
            "current_deadline",
            "priority",
            "frequency",
            "total_saved",
            "created_at",
            "updated_at",
            "user",
            "progress",
            "time_remaining",
            "is_completed",
            "is_deleted",
        ]
        read_only_fields = [
            "original_deadline",
            "created_at",
            "updated_at",
            "is_deleted",
            "is_completed",
            "progress",
            "time_remaining",
            "total_saved",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request and request.method in ["PATCH"]:
            self.fields["user"].read_only = True

    def validate_name(self, value):
        """Validate the name field."""
        user = self.context.get("request").user
        if not value or len(value.strip()) < 3:
            raise serializers.ValidationError("Name must be at least 3 characters long")
        value = value.strip()

        existing_plans = SavingsPlan.objects.filter(user=user, name__iexact=value)

        if self.instance:
            existing_plans = existing_plans.exclude(id=self.instance.id)
        if existing_plans.exists():
            raise serializers.ValidationError(
                "You already have a savings plan with this name."
            )

        return value

    def validate_target_amount(self, value):
        """Validate the target_amount field."""
        if value is None:
            raise serializers.ValidationError("Target amount is required")
        try:
            value = Decimal(str(value))
            if value <= 0:
                raise serializers.ValidationError(
                    "Target amount must be greater than 0"
                )
            return value
        except (TypeError, ValueError):
            raise serializers.ValidationError("Invalid amount format")

    def validate_current_deadline(self, value):
        """Validate the current_deadline field."""
        if value <= timezone.now().date():
            raise serializers.ValidationError("Deadline must be in the future")
        return value

    def validate_priority(self, value):
        """Validate the priority field."""
        valid_priorities = ["LOW", "MEDIUM", "HIGH"]
        if value and value.upper() not in valid_priorities:
            raise serializers.ValidationError(
                f"Priority must be one of: {', '.join(valid_priorities)}"
            )
        return value.upper() if value else "MEDIUM"

    def validate_frequency(self, value):
        """Validate the frequency field."""
        valid_frequencies = ["DAILY", "WEEKLY", "MONTHLY"]
        if value and value.upper() not in valid_frequencies:
            raise serializers.ValidationError(
                f"Frequency must be one of: {', '.join(valid_frequencies)}"
            )
        return value.upper() if value else "MONTHLY"

    def validate_user(self, user):
        """Validate the user field."""
        request = self.context.get("request")
        if not user.is_active:
            raise serializers.ValidationError("User not found")

        if not request.user.is_staff and user != request.user:
            raise serializers.ValidationError("You can only create plans for yourself")
        return user

    def validate(self, data):
        """Perform object-level validation."""
        # Set original_deadline for new instances
        if not self.instance and "current_deadline" in data:
            data["original_deadline"] = data["current_deadline"]

        return data

    def get_total_saved(self, obj):
        """Calculate and return the total saved amount for the savings plan."""
        return obj.get_total_saved()

    def get_progress(self, obj):
        """Calculate and return the progress of the savings plan."""
        total_saved = obj.get_total_saved()
        percentage = (
            round((total_saved / obj.target_amount) * 100, 2)
            if obj.target_amount > 0
            else 0
        )

        if percentage >= 100 and not obj.is_completed:
            obj.is_completed = True
            obj.save()  # Save the updated is_completed status
        elif percentage < 100 and obj.is_completed:
            obj.is_completed = False
            obj.save()  # Save the updated is_completed status

        return {
            "amount_saved": total_saved,
            "remaining_amount": obj.get_remaining_amount(),
            "percentage": percentage,
        }

    def get_time_remaining(self, obj):
        today = timezone.now().date()
        if obj.current_deadline < today:
            return "Deadline passed"
        days_remaining = (obj.current_deadline - today).days
        if days_remaining > 30:
            return f"{days_remaining // 30} month's left"
        elif days_remaining > 7:
            return f"{days_remaining // 7} week left"
        return f"{days_remaining} day left"
