from celery import shared_task
from datetime import datetime
from services.notification import send_mail
from django.conf import settings


@shared_task
def send_email_task(to_email, reset_link):
    """
    Send an email to the user with the password reset link.
    """
    subject = "Password Reset Request"
    dynamic_template_data = {
        "reset_link": reset_link,
    }
    send_mail(
        to_email,
        reset_link,
        subject=subject,
        dynamic_template_data=dynamic_template_data,
        dynamic_template_id=settings.SENDGRID_PASSWORD_RESET_TEMPLATE_ID,
    )
    return "Email sent successfully"
