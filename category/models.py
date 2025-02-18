import uuid
from django.db import models
from user.models import CustomUser
from utils.models import BaseModel
from utils.constants import TransactionType

class Category(BaseModel):
    """Creating table of Category"""

    name = models.CharField(max_length=100)
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="categories",
    )
    type = models.CharField(max_length=10, choices=TransactionType.CHOICES)
    is_predefined = models.BooleanField(default=False)

    def __str__(self):
        return str(self.name)
