import boto3
from django.conf import settings

sns_client = boto3.client(
    "sns",
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_REGION_NAME,
)

def subscribeEmail(email):
    response = sns_client.subscribe(
        TopicArn=settings.SNS_TOPIC_ARN,
        Protocol='email',
        Endpoint=email
    )
    return response

def subscribeSMS(phone_number):
    response = sns_client.subscribe(
        TopicArn=settings.SNS_TOPIC_ARN,
        Protocol='sms',
        Endpoint=phone_number
    )
    return response
