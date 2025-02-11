from django.contrib import admin

# Register your models here.
from .models import SavingsPlan, SavingsTransaction, DeadlineExtension

admin.site.register(SavingsPlan)
admin.site.register(SavingsTransaction)
admin.site.register(DeadlineExtension)
