from django.contrib.auth.models import BaseUserManager
from django.core.exceptions import ValidationError


class CustomUserManager(BaseUserManager):
    def create_user(self, email, username, password, **extra_fields):
        if not username:
            raise ValueError("Username must be present")
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        print(user)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        if not username.isalnum():
            raise ValidationError("Username must be alphanumeric.")

        # Ensure is_staff is True for superuser
        extra_fields.setdefault("is_staff", True)
        return self.create_user(email, username, password, **extra_fields)
