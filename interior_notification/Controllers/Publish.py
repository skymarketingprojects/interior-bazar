import boto3
import requests
from django.conf import settings
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.image import MIMEImage
import os



def publishToTopic(subject, message):
    sns_client = boto3.client(
        "sns",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION_NAME,
)
    response = sns_client.publish(
        TopicArn=settings.SNS_TOPIC_ARN,
        Message=message,
        Subject=subject
    )
    return response

# Create SNS client

def publishToUser(phone_number, message):
    try:
        sns = boto3.client("sns")

        response = sns.publish(
            PhoneNumber=phone_number,
            Message=message,
        )

        return response

    except Exception as e:
        print(f"Error sending SMS: {e}")
        return None

# Publish to email using SES

# def publishEmailToUser(senderEmail,recipientEmail, subject, body):
#     ses = boto3.client("ses", region_name= settings.AWS_REGION_NAME)

#     response = ses.send_email(
#         Source=senderEmail,
#         Destination={
#             "ToAddresses": [recipientEmail]
#         },
#         Message={
#             "Subject": {"Data": subject},
#             "Body": {"Text": {"Data": body}}
#         }
#     )
#     print(f"Email sent to {recipientEmail} with response: {response}")

#     return response

def publishEmailToUser(
    senderEmail,
    recipientEmail,
    subject,
    htmlBody=None,
    textBody=None,
    attachments=None,       # List of file paths for downloadable attachments
    inlineImages=None,     # Dict of inline images {"cid_name": "path/to/image.png"}
    regionName=settings.AWS_REGION_NAME
):
    """
    Send an HTML email with downloadable attachments and optional inline images.

    Args:
        sender_email (str): Sender email address (must be verified in SES sandbox).
        recipient_email (str): Recipient email address.
        subject (str): Subject line.
        html_body (str): HTML content.
        text_body (str, optional): Plain text fallback.
        attachments (list, optional): List of file paths for downloadable attachments.
        inline_images (dict, optional): {"cid_name": "path/to/image.png"} for embedding in HTML.
        region_name (str): AWS region for SES.

    Returns:
        dict: SES send_raw_email response.
    """

    try:
        ses = boto3.client("ses")

        # Root MIME message
        msg_root = MIMEMultipart("mixed")
        msg_root["Subject"] = subject
        msg_root["From"] = senderEmail
        msg_root["To"] = recipientEmail

        # Alternative part (text and HTML)
        msg_alt = MIMEMultipart("alternative")
        msg_root.attach(msg_alt)

        if textBody:
            msg_alt.attach(MIMEText(textBody, "plain", "utf-8"))
        if htmlBody:
            msg_alt.attach(MIMEText(htmlBody, "html", "utf-8"))

        # Inline images (for embedding)
        if inlineImages:
            related = MIMEMultipart("related")
            related.attach(msg_alt)
            for cid_name, path in inlineImages.items():
                with open(path, "rb") as img_file:
                    img = MIMEImage(img_file.read())
                    img.add_header("Content-ID", f"<{cid_name}>")
                    img.add_header("Content-Disposition", "inline", filename=os.path.basename(path))
                    related.attach(img)
            msg_root.attach(related)

        # Regular downloadable attachments
        if attachments:
            for path in attachments:
                with open(path, "rb") as file:
                    part = MIMEApplication(file.read())
                    part.add_header(
                        "Content-Disposition",
                        "attachment",
                        filename=os.path.basename(path)
                    )
                    msg_root.attach(part)

        # Send via SES
        response = ses.send_raw_email(
            Source=senderEmail,
            Destinations=[recipientEmail],
            RawMessage={"Data": msg_root.as_string()}
        )

        return response
    except Exception as e:
        print(f"Error sending email: {e}")
        return None


def WhatsappMessage(receiver_phone, body_text, button_url="https://interiorbazzar.com/"):
    try:

        ACCESS_TOKEN = settings.WHATSAPP_ACCESS_TOKEN
        PHONE_NUMBER_ID = settings.WHATSAPP_PHONE_NUMBER_ID
        print(f"{ACCESS_TOKEN} {PHONE_NUMBER_ID}")

        url = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"
        headers = {
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "Content-Type": "application/json",
        }

        payload = {
            "messaging_product": "whatsapp",
            "to": receiver_phone,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {
                    "text": body_text
                },
                "action": {
                    "buttons": [
                        {
                            "type": "url",
                            "url": button_url,
                            "title": "Open Link"
                        }
                    ]
                }
            }
        }

        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return {"success": True, "response": response.json()}
    except requests.exceptions.RequestException as e:
        print(f"Error sending WhatsApp message: {e}")
        return {"success": False, "error": str(e)}
