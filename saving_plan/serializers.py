
from rest_framework import serializers
from django.utils import timezone
from decimal import Decimal
from saving_plan.models import SavingsPlan
import re

from saving_plan.tasks import send_savings_plan_completion_notification
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
            "frequency",
            "total_saved",
            "created_at",
            "updated_at",
            "user",
            "progress",
            "time_remaining",
            "status",
            "is_deleted",
        ]
        read_only_fields = [
            "id",
            "original_deadline",
            "created_at",
            "updated_at",
            "is_deleted",
            "progress",
            "time_remaining",
            "total_saved",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request and request.method == "PATCH":
            self.fields["user"].read_only = True
    def _validate_name(self, value, user):
        """Helper function to validate name field."""
        value = value.strip()
        
        if not (3 <= len(value) <= 100):
            raise serializers.ValidationError("Name must be between 3 and 100 characters.")
        
        if not re.match(r"^[a-zA-Z0-9.,!?_() -]+$", value):
            raise serializers.ValidationError("Name contains invalid characters.")
        
        if SavingsPlan.objects.filter(name__iexact=value, user=user).exists():
            raise serializers.ValidationError("You already have a savings plan with this name.")
        
        return value

    def validate_target_amount(self, value):
        """Validate target amount."""
        
        if value <= 0:
            raise serializers.ValidationError("Target amount must be greater than 0.")
        
        if value > Decimal("999999999.99"):
            raise serializers.ValidationError("Amount is too large.")
        
        if self.instance:
            if self.instance.status == "COMPLETED":
                raise serializers.ValidationError("Cannot modify target amount of completed plan.")
            current_saved = self.instance.get_total_saved()
            if self.instance.status == "COMPLETED" and value < self.instance.target_amount:
                raise serializers.ValidationError("Cannot decrease target amount of completed plan.")
            
            if value < current_saved:
                raise serializers.ValidationError(
                    f"Target amount cannot be less than already saved: {current_saved}"
                )
        
        return value


    def validate_current_deadline(self, value):
        """Validate current deadline."""
        today = timezone.now().date()
        max_date = today.replace(year=today.year + 10)

        if value <= today:
            raise serializers.ValidationError("Deadline must be in the future.")
        if value > max_date:
            raise serializers.ValidationError("Deadline cannot be more than 10 years in the future.")
        if self.instance and self.instance.status == "COMPLETED":
            raise serializers.ValidationError("Cannot modify deadline of completed plan.")
        if self.instance and value < self.instance.original_deadline:
            raise serializers.ValidationError("New deadline cannot be earlier than the original deadline.")

        return value

    def validate_frequency(self, value):
        """Validate saving frequency."""
        valid_frequencies = {"DAILY", "WEEKLY", "MONTHLY"}
        value = value.upper() if value else "MONTHLY"
        if value not in valid_frequencies:
            raise serializers.ValidationError(f"Frequency must be one of: {', '.join(valid_frequencies)}.")
        return value

    def validate_user(self, user):
        """Validate user for savings plan."""
        request = self.context.get("request")
        current_user = request.user if request else None

        if not user.is_active:
            raise serializers.ValidationError("User not found.")

        if not current_user.is_staff and user != current_user:
            raise serializers.ValidationError("You can only create plans for yourself.")

        if current_user.is_staff and user.is_staff:
            raise serializers.ValidationError("Staff cannot create plans for other staff members.")

        return user
    
    def validate_status(self, value):
        """Validate status transitions."""
        valid_statuses = {"ACTIVE", "PAUSED", "COMPLETED"}
        
        if value not in valid_statuses:
            raise serializers.ValidationError(f"Invalid status. Must be one of {', '.join(valid_statuses)}.")
        
        if self.instance:
            current_status = self.instance.status
            current_saved = self.instance.get_total_saved()
            target_amount = self.instance.target_amount
            percentage = (current_saved / target_amount * 100) if target_amount > 0 else 0

            # Prevent reverting a completed plan
            if current_status == "COMPLETED" and value != "COMPLETED":
                raise serializers.ValidationError("Cannot change status of a completed plan.")
                
            # Prevent manual completion if target not reached
            if value == "COMPLETED" and percentage < 100:
                raise serializers.ValidationError("Cannot mark plan as completed until 100% of target is saved.")

        return value


    def validate(self, data):
        """Cross-field validation."""
        request = self.context.get("request")
        user = data.get("user", request.user)

        if self.instance is None:
            data["name"] = self._validate_name(data.get("name"), user)
            data["user"] = user

        elif "name" in data:
            data["name"] = self._validate_name(data["name"], self.instance.user)

        if not self.instance:
            if "current_deadline" in data:
                data["original_deadline"] = data["current_deadline"]
        if self.instance:
            current_saved = self.instance.get_total_saved()
            target_amount = data.get("target_amount", self.instance.target_amount)
            percentage = (current_saved / target_amount * 100) if target_amount > 0 else 0
            if percentage >= 100 and self.instance.status != "COMPLETED":
                print("jel.;p")
                print(self.instance.id)
                send_savings_plan_completion_notification.delay(self.instance.id)
                data["status"] = "COMPLETED"
            elif percentage < 100 and self.instance.status == "COMPLETED":
                data["status"] = "ACTIVE"

        return data

    def get_total_saved(self, obj):
        return obj.get_total_saved()

    def get_progress(self, obj):
        """Calculate progress percentage and remaining amount."""
        total_saved = obj.get_total_saved()
        try:
            percentage = round((total_saved / obj.target_amount) * 100, 2) if obj.target_amount > 0 else 0
        except (TypeError, ValueError):
            percentage = 0

        return {

            "remaining_amount": obj.get_remaining_amount(),
            "saved_amount_percentage": percentage,
        }
    
    def get_time_remaining(self, obj):
        """Calculate remaining time until deadline."""
        today = timezone.now().date()
        if obj.current_deadline < today:
            return "Deadline passed"
        days_remaining = (obj.current_deadline - today).days
        if days_remaining == 0:
            return "Due today"
        if days_remaining > 30:
            months = days_remaining // 30
            return f"{months} month{'s' if months > 1 else ''} left"
        if days_remaining > 7:
            weeks = days_remaining // 7
            return f"{weeks} week{'s' if weeks > 1 else ''} left"
        return f"{days_remaining} day{'s' if days_remaining > 1 else ''} left"
