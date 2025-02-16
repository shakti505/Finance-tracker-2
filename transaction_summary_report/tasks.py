from services.notification import send_mail
from celery import shared_task
from django.conf import settings
from transaction.models import Transaction
import csv, io
from utils.logging import logger
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from user.models import CustomUser
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


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
        """Creates a structured and well-styled PDF report of transactions"""
        output = io.BytesIO()
        doc = SimpleDocTemplate(output, pagesize=letter)
        styles = getSampleStyleSheet()

        # Custom styles
        title_style = styles["Title"]
        title_style.textColor = colors.darkblue

        subtitle_style = ParagraphStyle(
            "Subtitle",
            parent=styles["Heading2"],
            textColor=colors.darkred,
            spaceAfter=12,
        )

        normal_style = styles["Normal"]
        normal_style.spaceAfter = 8

        # Content List
        content = []

        # Title and Date Range
        content.append(Paragraph("Your Transaction History", title_style))
        content.append(Spacer(1, 10))
        content.append(
            Paragraph(f"From {self.start_date} to {self.end_date}", normal_style)
        )
        content.append(Spacer(1, 15))

        # Summary Table
        summary_data = [
            ["Total Income", f"RS {self.total_income:.2f}"],
            ["Total Expenses", f"RS {self.total_expenses:.2f}"],
        ]
        summary_table = Table(summary_data, colWidths=[250, 150])
        summary_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F5F5F5")),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                    ("GRID", (0, 0), (-1, -1), 1, colors.gray),
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("PADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        content.append(summary_table)
        content.append(Spacer(1, 20))

        # Transaction Table Generator
        def make_transaction_table(title, transactions):
            content.append(Paragraph(title, subtitle_style))
            content.append(Spacer(1, 10))

            data = [["Category", "Amount", "Date"]]
            for t in transactions:
                data.append([t["category"], f"RS {float(t['amount']):.2f}", t["date"]])

            table = Table(data, colWidths=[200, 120, 120])
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#003366")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("GRID", (0, 0), (-1, -1), 1, colors.black),
                        ("PADDING", (0, 0), (-1, -1), 6),
                    ]
                )
            )
            content.append(table)
            content.append(Spacer(1, 15))

        if self.income:
            make_transaction_table("Income Transactions", self.income)
        if self.expenses:
            make_transaction_table("Expense Transactions", self.expenses)

        # Footer with Page Number
        def footer(canvas, doc):
            canvas.saveState()
            footer_text = "Page %d" % doc.page
            canvas.setFont("Helvetica", 9)
            canvas.drawRightString(7.5 * inch, 0.5 * inch, footer_text)
            canvas.restoreState()

        doc.build(content, onLaterPages=footer, onFirstPage=footer)

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
