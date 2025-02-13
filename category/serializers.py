from rest_framework import serializers
from rest_framework.exceptions import ValidationError, PermissionDenied
from .models import Category
from django.utils.text import slugify


# def custom_slugify(value):
#     return slugify(value, allow_unicode=True).replace("-", " ")


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "user",
            "is_predefined",
            "type",
            "created_at",
            "updated_at",
            "is_deleted",
        ]
        read_only_fields = [
            "id",
            "is_predefined",
            "created_at",
            "updated_at",
            "is_deleted",
        ]

    def __init__(self, *args, **kwargs):
        """Dynamically set fields based on the request method."""
        super().__init__(*args, **kwargs)
        request = self.context.get("request")

        if request and request.method == "PATCH":
            self.fields["user"].read_only = True
            self.fields["type"].read_only = True

    def validate_user(self, user):
        """Validate the user field."""
        request = self.context["request"]

        if not user.is_active:
            raise serializers.ValidationError("User not found")

        if request.user == user:
            return user

        if not request.user.is_staff:
            raise serializers.ValidationError(
                "You can create categories for yourself only."
            )

        if user.is_staff:
            raise serializers.ValidationError(
                "You cannot create a category on behalf of another staff user."
            )

        return user

    def _validate_name(self, value, user, type):
        """Validate that the category name is unique for the determined user."""
        request = self.context.get("request")

        if (
            Category.objects.filter(
                name__iexact=value, user=user, is_deleted=False, type=type
            ).exists()
            or Category.objects.filter(
                name__iexact=value,
                is_deleted=False,
                is_predefined=True,
                type=type,
            ).exists()
        ):
            raise serializers.ValidationError(
                {
                    "name": f"A category with the name '{value}' already exists for the user or predefined."
                }
            )

        return value

    def validate(self, data):
        """Ensure the user field is handled correctly during creation and updates."""
        request = self.context.get("request")

        user = data.get("user", request.user)

        if self.instance is None:  # Creation
            data["name"] = self._validate_name(
                data.get("name", ""), user, data.get("type")
            )
            data["user"] = user
            data["is_predefined"] = user.is_staff
        else:
            if "name" in data:
                data["name"] = self._validate_name(
                    data["name"], self.instance.user, self.instance.type
                )

        return data
