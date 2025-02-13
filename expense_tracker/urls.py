from django.contrib import admin
from django.urls import path, include
from django.contrib import admin
from django.urls import path, include, re_path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Swagger schema definition
schema_view = get_schema_view(
    openapi.Info(
        title="Transaction API",
        default_version="v1",
        description="API documentation for Transactions",
        terms_of_service="https://www.shaktisingh.tech/",
        contact=openapi.Contact(email="support@example.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)
urlpatterns = [
    path("api/v1/", include("user.urls")),
    path("api/v1/transactions/", include("transaction.urls")),
    path("api/v1/categories/", include("category.urls")),
    path("api/v1/budget/", include("budget.urls")),
    path("api/v1/", include("saving_plan.urls")),
    path("api/v1/recurring-transactions/", include("recurring_transaction.urls")),
    path("api/v1/transaction-analytics/", include("transaction_summary_report.urls")),
    path("admin/", admin.site.urls),
    path(
        "swagger/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
    re_path(
        r"^swagger(?P<format>\.json|\.yaml)$",
        schema_view.without_ui(cache_timeout=0),
        name="schema-json",
    ),
]
