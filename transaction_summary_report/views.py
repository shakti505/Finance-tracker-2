from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError
from django.db.models import Sum, F
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from datetime import datetime
from utils.responses import (
    success_response,
    validation_error_response,
    not_found_error_response,
    success_single_response,
)
from transaction.models import Transaction
from user.models import CustomUser
from .serializers import TransactionReportSerializer
from utils.is_uuid import is_uuid
from .tasks import email_transaction_history
from rest_framework.permissions import IsAuthenticated


class BaseTransactionView(APIView):
    """Base view for transaction-related operations."""

    def get_target_user(self, request):
        user_id = request.query_params.get("user_id")
        if not request.user.is_staff:
            if "user_id" in request.query_params:
                raise ValidationError("Unauthorized to access other user's data")
            return request.user

        if not user_id or not is_uuid(user_id):
            raise ValidationError({"user_id": "Valid user_id required for staff"})
        user = CustomUser.objects.filter(id=user_id, is_staff=False).first()

        return user

    def get_date_range(self, request):
        try:
            start = datetime.strptime(
                request.query_params["start_date"], "%Y-%m-%d"
            ).date()
            end = datetime.strptime(request.query_params["end_date"], "%Y-%m-%d").date()
            return start, end
        except (KeyError, ValueError):
            raise ValidationError("Valid start_date and end_date (YYYY-MM-DD) required")

    def get_transactions(self, user, start_date, end_date):
        return Transaction.objects.filter(
            user=user, is_deleted=False, date__date__range=(start_date, end_date)
        )


class TransactionReportAPI(BaseTransactionView):
    """API view for generating transaction reports."""

    permission_classes = [IsAuthenticated]

    @method_decorator(cache_page(60 * 15))
    def get(self, request):
        try:
            user = self.get_target_user(request)
            start_date, end_date = self.get_date_range(request)
            transactions = self.get_transactions(user, start_date, end_date)
            credit_trans = transactions.filter(type="CREDIT")
            debit_trans = transactions.filter(type="DEBIT")

            return success_response(
                {
                    "total_income": credit_trans.aggregate(total=Sum("amount"))["total"]
                    or 0,
                    "total_expense": debit_trans.aggregate(total=Sum("amount"))["total"]
                    or 0,
                    "category_expense": debit_trans.values(
                        category_name=F("category__name")
                    )
                    .annotate(total=Sum("amount"))
                    .order_by("-total"),
                    "transactions": {
                        "credit_transactions": TransactionReportSerializer(
                            credit_trans.order_by("-date"), many=True
                        ).data,
                        "debit_transactions": TransactionReportSerializer(
                            debit_trans.order_by("-date"), many=True
                        ).data,
                    },
                }
            )
        except ValidationError as e:
            return validation_error_response(
                {"error": str(e)},
            )


class SpendingTrendsView(BaseTransactionView):
    """API view for generating spending trends report."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = self.get_target_user(request)
            start_date, end_date = self.get_date_range(request)
            transactions = self.get_transactions(user, start_date, end_date)

            credit_trans = transactions.filter(type="CREDIT")
            debit_trans = transactions.filter(type="DEBIT")

            total_income = credit_trans.aggregate(total=Sum("amount"))["total"] or 0
            total_expense = debit_trans.aggregate(total=Sum("amount"))["total"] or 0

            def get_category_data(queryset, total):
                data = queryset.values("category__name").annotate(total=Sum("amount"))
                return (
                    [
                        {
                            "category_name": item["category__name"],
                            "amount": float(item["total"]),
                            "percentage": round((item["total"] / total * 100), 2),
                        }
                        for item in data
                    ]
                    if total > 0
                    else []
                )

            return success_response(
                {
                    "start_date": str(start_date),
                    "end_date": str(end_date),
                    "total_income": float(total_income),
                    "total_expense": float(total_expense),
                    "income": get_category_data(credit_trans, total_income),
                    "expense": get_category_data(debit_trans, total_expense),
                }
            )
        except ValidationError as e:
            return validation_error_response(
                {"error": str(e)},
            )


class TransactionHistoryExportView(BaseTransactionView):
    """API view for exporting transaction history."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            file_format = request.query_params.get("file_format", "csv").lower()
            if file_format not in ["csv", "pdf"]:
                raise ValidationError("Invalid format. Use 'csv' or 'pdf'")
            user = self.get_target_user(request)
            start_date, end_date = self.get_date_range(request)
            transactions = self.get_transactions(user, start_date, end_date)
            if not transactions.exists():
                return not_found_error_response("No transactions found")

            email_transaction_history.delay(
                user.id, user.email, str(start_date), str(end_date), file_format
            )

            return success_single_response(
                {"detail": "Transaction history report sent to your email"}
            )
        except ValidationError as e:
            return validation_error_response(
                {"error": str(e)},
            )
