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
        fields = ["new_deadline", "reason", "savings_plan", "user"]

    def validate_new_deadline(self, value):
        if value <= timezone.now().date():
            raise serializers.ValidationError("New deadline must be in the future")
        return value

    def validate_user(self, data):
        request = self.context["request"]
        user = request.user
        if not user.is_staff and data != user:
            raise serializers.ValidationError(
                "You can only extend deadlines for yourself."
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
        savings_plan.status = "EXTENDED"
        savings_plan.save(update_fields=["current_deadline", "status"])
        return extension
