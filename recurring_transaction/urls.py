from django.urls import path
from .views import RecurringTransactionListCreateView, RecurringTransactionDetailView

urlpatterns = [
    path("", RecurringTransactionListCreateView.as_view(), name="category-list-create"),
    path(
        "<uuid:id>/",
        RecurringTransactionDetailView.as_view(),
        name="category-detail",
    ),
]
