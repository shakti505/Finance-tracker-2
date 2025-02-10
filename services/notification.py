# import os
# from sendgrid import SendGridAPIClient
# from sendgrid.helpers.mail import Mail
# from django.conf import settings


# def send_mail(
#     user_email, subject, dynamic_template_data, dynamic_template_id, attach=None
# ):
#     """
#     Send a budget alert email using SendGrid's dynamic template.

#     Args:
#         user_email (str): The recipient's email address.
#         subject (str): The subject of the email.
#         dynamic_template_data (dict): Data to populate the dynamic template.
#     """
#     # Set your SendGrid API key
#     SENDGRID_API_KEY = settings.SENDGRID_API_KEY  # Fetch from environment variables

#     message = Mail(
#         from_email="shakti@gkmit.co",
#         to_emails=user_email,
#         subject=subject,
#     )

#     message.template_id = dynamic_template_id
#     message.dynamic_template_data = dynamic_template_data

#     try:
#         # Send the email
#         sg = SendGridAPIClient(SENDGRID_API_KEY)
#         response = sg.send(message)
#         print(f"Email sent! Status code: {response.status_code}")
#     except Exception as e:
#         print(f"Error sending email: {e}")

import os
import base64
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Mail,
    Attachment,
    FileContent,
    FileName,
    FileType,
    Disposition,
)
from django.conf import settings


def send_mail(
    user_email, subject, dynamic_template_data, dynamic_template_id, attachment=None
):
    """
    Send an email using SendGrid's dynamic template with an optional file attachment.

    Args:
        user_email (str or list): The recipient's email address(es).
        subject (str): The subject of the email.
        dynamic_template_data (dict): Data to populate the dynamic template.
        dynamic_template_id (str): The ID of the SendGrid dynamic template.
        attachment (dict, optional): Attachment file details.
            Expected format:
            {
                "file_name": "example.pdf",
                "file_data": <binary file data>,
                "file_type": "application/pdf"
            }
    """

    # Set your SendGrid API key
    SENDGRID_API_KEY = settings.SENDGRID_API_KEY

    # Create the Mail object
    message = Mail(
        from_email="shakti@gkmit.co",
        to_emails=user_email,
        subject=subject,
    )

    # Set the dynamic template ID and data
    message.template_id = dynamic_template_id
    message.dynamic_template_data = dynamic_template_data

    # Add attachment if provided
    if attachment:
        file_name = attachment.get("file_name")
        file_data = attachment.get("file_data")
        file_type = attachment.get("file_type")

        if file_name and file_data and file_type:
            # Ensure file_data is in binary format before encoding
            if isinstance(file_data, str):
                file_data = file_data.encode()  # Convert string to bytes

            # Encode file data to base64
            encoded_file = base64.b64encode(file_data).decode()
            attached_file = Attachment(
                FileContent(encoded_file),
                FileName(file_name),
                FileType(file_type),
                Disposition("attachment"),
            )
            message.attachment = attached_file  # Attach file to email
    # Attach file to email

    try:
        # Send the email
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        print(f"Email sent! Status code: {response.status_code}")
        return True  # Indicate success
    except Exception as e:
        print(f"Error sending email: {e}")
        return False  # Indicate failure
