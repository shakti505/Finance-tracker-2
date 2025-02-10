import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


def send_mail(user_email, subject, dynamic_template_data, dyanmic_template_id):
    """
    Send a budget alert email using SendGrid's dynamic template.

    Args:
        user_email (str): The recipient's email address.
        subject (str): The subject of the email.
        dynamic_template_data (dict): Data to populate the dynamic template.
    """
    # Set your SendGrid API key
    SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")  # Fetch from environment variables

    message = Mail(
        from_email="shakti@gkmit.co",
        to_emails=user_email,
        subject=subject,
    )

    message.template_id = dyanmic_template_id

    message.dynamic_template_data = dynamic_template_data

    try:
        # Send the email
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        print(f"Email sent! Status code: {response.status_code}")
    except Exception as e:
        print(f"Error sending email: {e}")
