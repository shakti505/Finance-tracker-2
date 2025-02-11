# from django.shortcuts import render

# # Create your views here.
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status
# from rest_framework.exceptions import ValidationError
# from django.db.models import Sum, F
# from django.utils.decorators import method_decorator
# from django.views.decorators.cache import cache_page
# from datetime import datetime

# from transaction.models import Transaction

# from .serializers import (
#     TransactionReportSerializer,
# )
# from user.models import CustomUser
# from utils.is_uuid import is_uuid
# from .tasks import send_transaction_history_email


# def parse_and_validate_dates(request):
#     """Helper function to parse and validate start_date and end_date from query parameters."""
#     start_date = request.query_params.get("start_date")
#     end_date = request.query_params.get("end_date")

#     if not start_date or not end_date:
#         return (
#             None,
#             None,
#             Response(
#                 {"error": "Both start_date and end_date are required"},
#                 status=status.HTTP_400_BAD_REQUEST,
#             ),
#         )

#     try:
#         start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
#         end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
#     except ValueError:
#         return (
#             None,
#             None,
#             Response(
#                 {"error": "Invalid date format. Use YYYY-MM-DD"},
#                 status=status.HTTP_400_BAD_REQUEST,
#             ),
#         )

#     return start_date, end_date, None


# def fetch_transactions(user, start_date, end_date):
#     """Helper function to retrieve transactions for a user within a date range."""
#     return Transaction.objects.filter(
#         user=user, is_deleted=False, date__date__range=(start_date, end_date)
#     )


# def calculate_totals(transactions, transaction_type):
#     """Helper function to calculate total income or expenses."""
#     return (
#         transactions.filter(type=transaction_type).aggregate(total=Sum("amount"))[
#             "total"
#         ]
#         or 0.00
#     )


# def group_transactions_by_category(transactions):
#     """Helper function to group transactions by category and calculate total amount per category."""
#     return list(
#         transactions.values(category_name=F("category__name"))
#         .annotate(total=Sum("amount"))
#         .order_by("-total")
#     )


# def calculate_percentage(data_list, total_amount, percentage_key):
#     """Helper function to calculate category percentage contribution."""
#     return [
#         {
#             "category_name": entry["category__name"],
#             "amount": float(entry["total"]),
#             percentage_key: round((entry["total"] / total_amount) * 100, 2),
#         }
#         for entry in data_list
#         if total_amount > 0
#     ]


# def get_target_user(request):
#     """
#     Determines the target user for the request based on authentication and permissions.

#     - Normal users can only fetch their own data.
#     - Staff users must pass 'user_id' and can fetch only normal users' data.
#     - Prevents staff from accessing other staff users' data.
#     """
#     user_id = request.query_params.get("user_id")
#     if not request.user.is_staff:
#         if "user_id" in request.query_params.keys():
#             raise ValidationError(
#                 "You are not authorized to access another user's data."
#             )
#         return request.user

#     else:
#         if not user_id:
#             raise ValidationError("Staff users must provide a user_id of normal user.")

#         if not is_uuid(user_id):
#             raise ValidationError("Invalid user_id format.")
#         try:
#             target_user = CustomUser.objects.get(
#                 id=user_id, is_staff=False
#             )  # Ensure target is a normal user
#         except CustomUser.DoesNotExist:
#             raise ValidationError("Invalid user_id or user is not a normal user.")

#         return target_user


# class TransactionReportAPI(APIView):
#     @method_decorator(cache_page(60 * 15))
#     def get(self, request):
#         start_date, end_date, error_response = parse_and_validate_dates(request)
#         if error_response:
#             return error_response

#         try:
#             target_user = get_target_user(request)
#         except ValidationError as e:
#             return Response(
#                 {"error": str(e.detail[0])}, status=status.HTTP_400_BAD_REQUEST
#             )

#         transactions = fetch_transactions(target_user, start_date, end_date)
#         print(transactions)
#         total_income = calculate_totals(transactions, "credit")
#         total_expense = calculate_totals(transactions, "debit")

#         category_expense = group_transactions_by_category(
#             transactions.filter(type="debit")
#         )

#         credit_transactions = TransactionReportSerializer(
#             transactions.filter(type="credit").order_by("-date"), many=True
#         ).data

#         debit_transactions = TransactionReportSerializer(
#             transactions.filter(type="debit").order_by("-date"), many=True
#         ).data

#         response_data = {
#             "total_income": total_income,
#             "total_expense": total_expense,
#             "category_expense": category_expense,
#             "transactions": {
#                 "credit_transactions": credit_transactions,
#                 "debit_transactions": debit_transactions,
#             },
#         }

#         return Response(response_data, status=status.HTTP_200_OK)


# class SpendingTrendsView(APIView):
#     def get(self, request):
#         start_date, end_date, error_response = parse_and_validate_dates(request)
#         if error_response:
#             return error_response

#         try:
#             target_user = get_target_user(request)
#         except ValidationError as e:
#             return Response(
#                 {"error": str(e.detail[0])}, status=status.HTTP_400_BAD_REQUEST
#             )

#         transactions = fetch_transactions(target_user, start_date, end_date)

#         total_income = calculate_totals(transactions, "credit")
#         total_expense = calculate_totals(transactions, "debit")

#         income_data = group_transactions_by_category(transactions.filter(type="credit"))
#         expense_data = group_transactions_by_category(transactions.filter(type="debit"))

#         income_list = calculate_percentage(income_data, total_income, "percentage")
#         expense_list = calculate_percentage(expense_data, total_expense, "percentage")

#         response_data = {
#             "start_date": str(start_date),
#             "end_date": str(end_date),
#             "total_income": float(total_income),
#             "total_expense": float(total_expense),
#             "income": income_list,
#             "expense": expense_list,
#         }

#         return Response(response_data, status=status.HTTP_200_OK)


# class TransactionHistoryExportView(APIView):
#     def get(self, request):
#         try:
#             # Get parameters from query params
#             file_format = request.query_params.get("file_format", "csv").lower()

#             start_date, end_date, error_response = parse_and_validate_dates(request)
#             # ensures start is provided or not and its format is correct or not
#             if error_response:
#                 return error_response

#             if file_format not in ["csv", "pdf"]:
#                 return Response(
#                     {"error": "Invalid format. Use 'csv' or 'pdf'"},
#                     status=status.HTTP_400_BAD_REQUEST,
#                 )

#             try:
#                 target_user = get_target_user(request)
#             except ValidationError as e:
#                 return Response(
#                     {"error": str(e.detail[0])}, status=status.HTTP_400_BAD_REQUEST
#                 )

#             transactions = fetch_transactions(target_user, start_date, end_date)

#             if not transactions.exists():
#                 return Response(
#                     {"error": "No transactions found for the given date range"},
#                     status=status.HTTP_404_NOT_FOUND,
#                 )

#             # Trigger Celery task for email sending
#             send_transaction_history_email.delay(
#                 target_user.id,
#                 target_user.email,
#                 str(start_date),
#                 str(end_date),
#                 file_format,
#             )

#             return Response(
#                 {
#                     "message": "Your transaction history report has been sent to your email"
#                 },
#                 status=status.HTTP_200_OK,
#             )

#         except Exception as e:
#             return Response(
#                 {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )


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


class BaseTransactionView(APIView):
    def get_target_user(self, request):
        user_id = request.query_params.get("user_id")
        if not request.user.is_staff:
            if "user_id" in request.query_params:
                raise ValidationError("Unauthorized to access other user's data")
            return request.user

        if not user_id or not is_uuid(user_id):
            raise ValidationError("Valid user_id required for staff")
        return CustomUser.objects.get(id=user_id, is_staff=False)

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
    @method_decorator(cache_page(60 * 15))
    def get(self, request):
        try:
            user = self.get_target_user(request)
            start_date, end_date = self.get_date_range(request)
            transactions = self.get_transactions(user, start_date, end_date)

            credit_trans = transactions.filter(type="credit")
            debit_trans = transactions.filter(type="debit")

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
    def get(self, request):
        try:
            user = self.get_target_user(request)
            start_date, end_date = self.get_date_range(request)
            transactions = self.get_transactions(user, start_date, end_date)

            credit_trans = transactions.filter(type="credit")
            debit_trans = transactions.filter(type="debit")

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
    def get(self, request):
        try:
            file_format = request.query_params.get("file_format", "csv").lower()
            if file_format not in ["csv", "pdf"]:
                raise ValidationError("Invalid format. Use 'csv' or 'pdf'")
            user = self.get_target_user(request)
            start_date, end_date = self.get_date_range(request)
            transactions = self.get_transactions(user, start_date, end_date)

            if not transactions.exists():
                return not_found_error_response(
                    {"error": "No transactions found"},
                )

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
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
