from rest_framework import serializers
from transaction.models import Transaction


class TransactionReportSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source="category.name")
    date = serializers.DateTimeField("date")

    class Meta:
        model = Transaction
        fields = ["category", "amount", "date"]

    def get_date(self, obj):
        return obj.date.date()
