from django.urls import path
from .views import SavingsPlanListCreateAPIView, SavingsPlanDetailAPIView


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

]
