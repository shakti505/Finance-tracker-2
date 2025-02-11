from django.contrib.auth.models import BaseUserManager
from django.core.exceptions import ValidationError


class CustomUserManager(BaseUserManager):
    def create_user(self, email, username, password, **extra_fields):
        if not username:
            raise ValueError("Username must be present")
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        # Ensure is_staff is True for superuser
        extra_fields.setdefault("is_staff", True)
        # Ensure is_superuser is True for superuser
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, username, password, **extra_fields)
