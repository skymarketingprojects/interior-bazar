import boto3
from django.conf import settings

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
import boto3

# Create SNS client

def publishToUser(phone_number, message):
    sns = boto3.client("sns")

    response = sns.publish(
        PhoneNumber=phone_number,
        Message=message,
    )

    return response

# Publish to email using SES

def publishEmailToUser(senderEmail,recipientEmail, subject, body):
    ses = boto3.client("ses", region_name= settings.AWS_REGION_NAME)

    response = ses.send_email(
        Source=senderEmail,
        Destination={
            "ToAddresses": [recipientEmail]
        },
        Message={
            "Subject": {"Data": subject},
            "Body": {"Text": {"Data": body}}
        }
    )

    return response