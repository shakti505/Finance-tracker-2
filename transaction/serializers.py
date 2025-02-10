from rest_framework import serializers
from .models import Transaction
from utils.is_uuid import is_uuid
from user.models import CustomUser


class TransactionSerializer(serializers.ModelSerializer):
    """Serializer for Transaction model."""

    class Meta:
        model = Transaction
        fields = [
            "id",
            "type",
            "amount",
            "category",
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
        if category.is_deleted:
            raise serializers.ValidationError("Category not found.")
        type = self._get_transaction_type()
        user = self._get_transaction_user()
        if not category.is_predefined and category.user != user:
            raise serializers.ValidationError(
                "Category does not belong to the provided user."
            )
        if category.type != type:
            raise serializers.ValidationError(
                "Category type does not match transaction type."
            )
        return category
