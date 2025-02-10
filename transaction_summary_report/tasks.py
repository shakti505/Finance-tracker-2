from rest_framework.response import Response
from services.notification import send_mail
from celery import shared_task
from django.conf import settings
from transaction.models import Transaction
import csv
import io
from utils.logging import logger
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from user.models import CustomUser


# @shared_task
# def send_transaction_history_email(
#     user_id,
#     user_email,
#     start_date,
#     end_date,
#     file_format,
# ):
#     """Celery task to generate and send transaction history via email asynchronously."""

#     user = CustomUser.objects.get(id=user_id)
#     # Filter transactions for the authenticated user
#     transactions = (
#         Transaction.objects.filter(
#             user=user,
#             is_deleted=False,
#             date__date__range=(start_date, end_date),
#         )
#         .select_related(
#             "category",
#         )
#         .order_by("-date")
#     )

#     # if not transactions.exists():
#     #     return {"error": "No transactions found for the given date range"}

#     credit_transactions = [
#         {
#             "category": txn.category.name,  # Fetch category name
#             "amount": str(txn.amount),  #
#             "date": txn.date.date().isoformat(),
#         }
#         for txn in transactions.filter(type="credit")
#     ]

#     debit_transactions = [
#         {
#             "category": txn.category.name,  # Fetch category name
#             "amount": str(txn.amount),
#             "date": txn.date.date().isoformat(),
#         }
#         for txn in transactions.filter(type="debit")
#     ]

#     # Generate file
#     file_data = None
#     file_name = f"transactions_history_{start_date}_{end_date}.{file_format}"

#     try:
#         # Generate file in memory
#         if file_format == "csv":
#             file_data = generate_csv_transaction_history(
#                 start_date, end_date, credit_transactions, debit_transactions
#             )
#         elif file_format == "pdf":
#             file_data = generate_pdf_transaction_history(
#                 start_date, end_date, credit_transactions, debit_transactions
#             )

#         dynamic_template_data = {
#             "subject": "Transaction History Report",
#             "user_name": user.name,
#             "start_date": start_date,
#             "end_date": end_date,
#         }
#         attachment = {
#             "file_name": file_name,
#             "file_data": file_data.getvalue(),
#             "file_type": f"application/{file_format}",
#         }
#         # Prepare email
#         email_subject = "Your Transaction History"
#         email = send_mail(
#             [user_email],
#             email_subject,
#             dynamic_template_data=dynamic_template_data,
#             dynamic_template_id=settings.SENDGRID_TRANSACTION_HISTORY_TEMPLATE_ID,
#             attachment=attachment,
#         )
#         if not email:
#             return {"error": "Failed to send email"}

#         return {"message": "Transaction history sent via email successfully"}

#     except Exception as e:
#         return {"error": str(e)}


# def generate_csv_transaction_history(
#     start_date, end_date, credit_transactions, debit_transactions
# ):
#     """Generates a CSV file for transaction history in memory."""
#     output = io.StringIO()
#     writer = csv.writer(output)

#     # Calculate total amounts
#     total_credit = sum(float(txn["amount"]) for txn in credit_transactions)
#     total_debit = sum(float(txn["amount"]) for txn in debit_transactions)

#     # Metadata
#     writer.writerow(["Transaction History Report"])
#     writer.writerow([f"Date Range: {start_date} to {end_date}"])
#     writer.writerow([])  # Blank line

#     # Total Amounts
#     writer.writerow(["Total Income", total_credit])
#     writer.writerow(["Total Expense", total_debit])
#     writer.writerow([])  # Blank line

#     # Credit Transactions
#     writer.writerow(["Credit Transactions"])
#     writer.writerow(["Category", "Amount", "Date"])
#     for txn in credit_transactions:
#         writer.writerow([txn["category"], txn["amount"], txn["date"]])

#     writer.writerow([])  # Blank line

#     # Debit Transactions
#     writer.writerow(["Debit Transactions"])
#     writer.writerow(["Category", "Amount", "Date"])
#     for txn in debit_transactions:
#         writer.writerow([txn["category"], txn["amount"], txn["date"]])

#     output.seek(0)  # Move cursor to start for reading
#     return output


# def generate_pdf_transaction_history(
#     start_date, end_date, credit_transactions, debit_transactions
# ):
#     """Generates a well-formatted PDF file for transaction history using ReportLab's Platypus."""

#     output = io.BytesIO()
#     doc = SimpleDocTemplate(output, pagesize=letter)
#     elements = []  # Holds all PDF elements

#     styles = getSampleStyleSheet()

#     # Title
#     elements.append(Paragraph("Transaction History Report", styles["Title"]))
#     elements.append(Spacer(1, 12))  # Spacer for better readability

#     # Date Range
#     elements.append(
#         Paragraph(f"Date Range: {start_date} to {end_date}", styles["Normal"])
#     )
#     elements.append(Spacer(1, 12))

#     # Calculate total amounts
#     total_credit = sum(float(txn["amount"]) for txn in credit_transactions)
#     total_debit = sum(float(txn["amount"]) for txn in debit_transactions)

#     # Total Income & Expense Table
#     total_table_data = [
#         ["Total Income", f"{total_credit:.2f}"],
#         ["Total Expense", f"{total_debit:.2f}"],
#     ]

#     total_table = Table(total_table_data, colWidths=[200, 150])
#     total_table.setStyle(
#         TableStyle(
#             [
#                 ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
#                 ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
#                 ("ALIGN", (0, 0), (-1, -1), "CENTER"),
#                 ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
#                 ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
#             ]
#         )
#     )

#     elements.append(total_table)
#     elements.append(Spacer(1, 12))

#     # Function to generate transactions table
#     def create_transaction_table(title, transactions):
#         elements.append(Paragraph(title, styles["Heading2"]))
#         elements.append(Spacer(1, 8))

#         table_data = [["Category", "Amount", "Date"]]
#         for txn in transactions:
#             table_data.append([txn["category"], txn["amount"], txn["date"]])

#         transaction_table = Table(table_data, colWidths=[150, 100, 100, 100])
#         transaction_table.setStyle(
#             TableStyle(
#                 [
#                     ("BACKGROUND", (0, 0), (-1, 0), colors.lightblue),
#                     ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
#                     ("ALIGN", (0, 0), (-1, -1), "CENTER"),
#                     ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
#                     ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
#                     ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
#                 ]
#             )
#         )

#         elements.append(transaction_table)
#         elements.append(Spacer(1, 12))

#     # Add Credit Transactions Table
#     create_transaction_table("Credit Transactions", credit_transactions)

#     # Add Debit Transactions Table
#     create_transaction_table("Debit Transactions", debit_transactions)

#     # Build PDF
#     doc.build(elements)
#     output.seek(0)
#     return output

from datetime import date
from celery import shared_task
from django.conf import settings
import csv
import io
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet


class TransactionReport:
    """Handles creating transaction reports in CSV or PDF format"""

    def __init__(self, start_date, end_date, transactions):
        self.start_date = start_date
        self.end_date = end_date

        # Split transactions into income and expenses
        self.income = [t for t in transactions if t["type"] == "credit"]
        self.expenses = [t for t in transactions if t["type"] == "debit"]

        # Calculate totals
        self.total_income = sum(float(t["amount"]) for t in self.income)
        self.total_expenses = sum(float(t["amount"]) for t in self.expenses)

    def make_csv(self):
        """Creates a CSV report of transactions"""
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header info
        writer.writerow(["Your Transaction History"])
        writer.writerow([f"From {self.start_date} to {self.end_date}"])
        writer.writerow([])

        # Write summary
        writer.writerow(["Total Income", f"RS{self.total_income:.2f}"])
        writer.writerow(["Total Expenses", f"RS{self.total_expenses:.2f}"])
        writer.writerow([])

        # Write income
        writer.writerow(["Income"])
        writer.writerow(["Category", "Amount", "Date"])
        for t in self.income:
            writer.writerow([t["category"], f"{float(t['amount']):.2f}", t["date"]])
        writer.writerow([])

        # Write expenses
        writer.writerow(["Expenses"])
        writer.writerow(["Category", "Amount", "Date"])
        for t in self.expenses:
            writer.writerow([t["category"], f"{float(t['amount']):.2f}", t["date"]])

        output.seek(0)
        return output

    def make_pdf(self):
        """Creates a nice-looking PDF report of transactions"""
        output = io.BytesIO()
        doc = SimpleDocTemplate(output, pagesize=letter)
        styles = getSampleStyleSheet()
        content = []

        # Add title and date range
        content.append(Paragraph("Your Transaction History", styles["Title"]))
        content.append(Spacer(1, 12))
        content.append(
            Paragraph(f"From {self.start_date} to {self.end_date}", styles["Normal"])
        )
        content.append(Spacer(1, 12))

        # Add summary table
        summary_data = [
            ["Total Income", f"{self.total_income:.2f}"],
            ["Total Expenses", f"{self.total_expenses:.2f}"],
        ]
        summary_table = Table(summary_data, colWidths=[200, 150])
        summary_table.setStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.lightgrey),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]
        )
        content.append(summary_table)
        content.append(Spacer(1, 20))

        # Helper function to create transaction tables
        def make_transaction_table(title, transactions):
            content.append(Paragraph(title, styles["Heading2"]))
            content.append(Spacer(1, 12))

            data = [["Category", "Amount", "Date"]]
            for t in transactions:
                data.append([t["category"], f"RS{float(t['amount']):.2f}", t["date"]])

            table = Table(data, colWidths=[200, 100, 100])
            table.setStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightblue),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ]
            )
            content.append(table)
            content.append(Spacer(1, 20))

        # Add income and expense tables
        make_transaction_table("Income", self.income)
        make_transaction_table("Expenses", self.expenses)

        doc.build(content)
        output.seek(0)
        return output


@shared_task(max_retries=3)
def email_transaction_history(user_id, user_email, start_date, end_date, file_type):
    """Emails a transaction report to the user"""
    try:
        # Get user's transactions
        user = CustomUser.objects.get(id=user_id)
        transactions = Transaction.objects.filter(
            user=user, is_deleted=False, date__date__range=(start_date, end_date)
        ).select_related("category")

        # Format transactions for the report
        formatted_transactions = []
        for t in transactions:
            formatted_transactions.append(
                {
                    "type": t.type,
                    "category": t.category.name,
                    "amount": str(t.amount),
                    "date": t.date.date().isoformat(),
                }
            )

        # Create the report
        report = TransactionReport(start_date, end_date, formatted_transactions)
        if file_type == "csv":
            file_data = report.make_csv()
        else:
            file_data = report.make_pdf()

        # Send email
        email_data = {
            "subject": "Transaction History Report",
            "user_name": user.name,
            "start_date": start_date,
            "end_date": end_date,
        }

        attachment = {
            "file_name": f"transactions_{start_date}_{end_date}.{file_type}",
            "file_data": file_data.getvalue(),
            "file_type": f"application/{file_type}",
        }

        success = send_mail(
            [user_email],
            "Your Transaction History",
            dynamic_template_data=email_data,
            dynamic_template_id=settings.SENDGRID_TRANSACTION_HISTORY_TEMPLATE_ID,
            attachment=attachment,
        )

        if not success:
            raise Exception("Couldn't send email")

        return {"message": "Report sent to your email!"}

    except Exception as e:
        logger.error(f"Failed to send transaction report: {str(e)}")
        # Retry the task if it fails
        raise email_transaction_history.retry(exc=e)
