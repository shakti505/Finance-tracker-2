from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
import uuid
from .managers import CustomUserManager
from django.core.validators import (
    MinLengthValidator,
    RegexValidator,
)
from utils.models import BaseModel


class CustomUser(AbstractBaseUser, PermissionsMixin):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    username = models.CharField(
        max_length=50,
        unique=True,
    )
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = CustomUserManager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    def __str__(self):
        return self.email


class ActiveTokens(BaseModel):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="token")
    token = models.CharField(max_length=1024, unique=True)

    def __str__(self):
        return f"{self.user}"
