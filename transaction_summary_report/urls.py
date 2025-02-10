from django.urls import path
from .views import (
    TransactionReportAPI,
    SpendingTrendsView,
    TransactionHistoryExportView,
)

urlpatterns = [
    path("", TransactionReportAPI.as_view(), name="transaction-report"),
    path("trends/", SpendingTrendsView.as_view(), name="transaction-report"),
    path("summary/", TransactionHistoryExportView.as_view(), name="transaction-report"),
]
