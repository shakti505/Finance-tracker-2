from django.contrib import admin
from .models import CustomUser, ActiveTokens

# Register your models here.

admin.site.register(CustomUser)
admin.site.register(ActiveTokens)
