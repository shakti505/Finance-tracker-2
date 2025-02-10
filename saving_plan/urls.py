from django.urls import path
from .views.saving_plan import SavingsPlanListCreateAPIView, SavingsPlanDetailAPIView
from .views.saving_plan_deadline_extension import ExtendDeadlineAPIView
from .views.saving_transaction import (
    SavingsTransactionListCreateAPIView,
    SavingsTransactionDetailAPIView,
)

urlpatterns = [
    path(
        "savings-plans/",
        SavingsPlanListCreateAPIView.as_view(),
        name="savings-plan-list-create",
    ),
    path(
        "savings-plans/<uuid:id>/",
        SavingsPlanDetailAPIView.as_view(),
        name="savings-plan-detail",
    ),
    path(
        "savings-plans/extend-deadline/",
        ExtendDeadlineAPIView.as_view(),
        name="extend-deadline",
    ),
    path(
        "savings-transactions/",
        SavingsTransactionListCreateAPIView.as_view(),
        name="savings-transaction-list-create",
    ),
    path(
        "savings-transactions/<uuid:id>/",
        SavingsTransactionDetailAPIView.as_view(),
        name="savings-transaction-detail",
    ),
]
