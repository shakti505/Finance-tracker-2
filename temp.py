from rest_framework import serializers
from .models import Category
import re


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "user", "is_predefined"]
        read_only_fields = ["id", "is_predefined"]

    def normalize_category_name(self, name: str) -> str:
        """Normalize category name by removing extra spaces and punctuation."""
        name = name.strip().lower()
        name = re.sub(r"[^\w\s]", "", name)
        name = re.sub(r"\s+", " ", name)
        return name

    def validate_user(self, user):
        """Validate the user field."""

        request = self.context["request"]

        # During update, the user field cannot be modified
        if self.instance is not None:
            raise serializers.ValidationError(
                "You cannot modify the user field during an update."
            )
        # If the user is not staff, they cannot pass a user in the request
        if not request.user.is_staff:
            raise serializers.ValidationError(
                "You cannot pass the user in this request."
            )

        if user is None:
            raise serializers.ValidationError("User field cannot be blank.")

        if user.is_active == False:
            raise serializers.ValidationError("User not found")

        return user

    def validate_category_name(self, value, user):
        """Ensure the category name is unique for the user or predefined categories."""
        normalized_value = self.normalize_category_name(value)

        if (
            Category.objects.filter(
                name__iexact=normalized_value,
                user=user,
                is_deleted=False,
            ).exists()
            or Category.objects.filter(
                name__iexact=normalized_value, is_predefined=True, is_deleted=False
            ).exists()
        ):
            raise serializers.ValidationError({"name": "This category already exists."})
        return normalized_value

    def validate(self, data):
        """
        Validate category data, ensuring the name and user fields are correct.
        """
        request = self.context["request"]
        # category_name = data["name"]

        if self.instance is None:
            # when there is create request

            user = data.get("user", request.user)

            if "name" in data:
                data["name"] = self.validate_category_name(data["name"], user)

            data["user"] = user
            data["is_predefined"] = user.is_staff

        else:
            # when there is update request
            if "name" in data:  # Only validate name if provided
                data["name"] = self.validate_category_name(
                    data["name"], self.instance.user
                )

        return data

    def __init__(self, *args, **kwargs):
        """Override __init__ to make the user field read-only during patch requests."""
        super().__init__(*args, **kwargs)

        request = self.context.get("request", None)
        if request and request.method == "PATCH":
            # Set the user field as read-only during patch (update) requests
            self.fields["user"].read_only = True

    def create(self, validated_data):
        """Create a new category."""
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Update an existing category."""
        return super().update(instance, validated_data)
