from rest_framework import serializers
from django.utils import timezone
from saving_plan.models import DeadlineExtension
from user.models import CustomUser
from utils.is_uuid import is_uuid


class ExtendDeadlineSerializer(serializers.ModelSerializer):
    new_deadline = serializers.DateField()
    reason = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = DeadlineExtension
        fields = [
            "new_deadline",
            "reason",
            "savings_plan",
            "user",
            "id",
            "created_at",
            "updated_at",
            "is_deleted",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "is_deleted"]

    def validate_new_deadline(self, value):
        savings_plan = self.context["savings_plan"]  # Get the savings plan from context
        if value <= timezone.now().date():
            raise serializers.ValidationError("New deadline must be in the future.")

        if value <= savings_plan.current_deadline:
            raise serializers.ValidationError(
                "New deadline must be after the current deadline."
            )

        return value

    def validate_user(self, user):
        """Ensure valid user selection based on user role."""
        request_user = self.context["request"].user

        if not user.is_active:
            raise serializers.ValidationError("User not found.")

        if not request_user.is_staff and user != request_user:
            raise serializers.ValidationError(
                "You can only extend your own savings plans"
            )
        return user

    def _get_saving_plan_user(self):
        """Helper method to get and validate the transaction user."""

        if "user" not in self.initial_data:
            return None

        user_id = self.initial_data.get("user")

        if not is_uuid(user_id):
            return None

        user = CustomUser.objects.filter(id=user_id, is_active=True).first()
        return user

    def validate_savings_plan(self, data):
        user = self.initial_data.get("user")
        saving_user = data.user
        user_instance = self._get_saving_plan_user()
        if user_instance != saving_user:
            raise serializers.ValidationError(
                "You can only extend your own savings plans"
            )
        return data

    def create(self, validated_data):
        savings_plan = self.context["savings_plan"]
        user = self.initial_data["user"]
        extension = DeadlineExtension.objects.create(
            savings_plan=savings_plan,
            previous_deadline=savings_plan.current_deadline,
            new_deadline=validated_data["new_deadline"],
            reason=validated_data.get("reason", ""),
            user_id=user,
        )
        savings_plan.current_deadline = validated_data["new_deadline"]
        savings_plan.save()
        return extension
