import uuid
import boto3
from django.conf import settings
from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.MyMethods import MY_METHODS

class imageUrlGenrator:
    def GenerateImageUploadUrl(self, FileName, FileType, ImageIntent):
        try:
            s3 = boto3.client(
                "s3",
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_S3_REGION_NAME
            )

            if ImageIntent == "ProfileImage":
                FolderPath = FilePath.ProfileImage()

            elif ImageIntent == "BusinessPrimaryImage":
                FolderPath = FilePath.BusinessPrimaryImage()
            elif ImageIntent == "BusinessBadge":
                FolderPath = FilePath.BusinessBadge()

            elif ImageIntent == "BusinessSecondaryImages":
                FolderPath = FilePath.BusinessSecondaryImages()

            elif ImageIntent == "LeadQueryAttachment":
                FolderPath = FilePath.LeadQueryAttachment()

            elif ImageIntent == "SubscriptionCover":
                FolderPath = FilePath.SubscriptionCover()

            elif ImageIntent == "SubscriptionVideo":
                FolderPath = FilePath.SubscriptionVideo()

            elif ImageIntent == "SubscriptionPDF":
                FolderPath = FilePath.SubscriptionPDF()

            elif ImageIntent == "BlogCover":
                FolderPath = FilePath.BlogCover()

            elif ImageIntent == "ContactAttachment":
                FolderPath = FilePath.ContactAttachment()

            elif ImageIntent == "PaymentQR":
                FolderPath = FilePath.PaymentQR()

            elif ImageIntent == "Banner":
                FolderPath = FilePath.Banner()

            elif ImageIntent == "StockMedia":
                FolderPath = FilePath.StockMedia()

            else:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=f"Unsupported ImageIntent: {ImageIntent}",
                    data={},
                    code=RESPONSE_CODES.error,
                )

            UniqueFileName = f"{FolderPath}{uuid.uuid4()}_{FileName}"

            PresignedUrl = s3.generate_presigned_url(
                "put_object",
                Params={
                    "Bucket": settings.AWS_STORAGE_BUCKET_NAME,
                    "Key": UniqueFileName,
                    "ContentType": FileType,
                },
                ExpiresIn=300
            )

            FileUrl = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{UniqueFileName}"

            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.presigned_url_success,
                data={
                    "uploadUrl": PresignedUrl,
                    "fileUrl": FileUrl
                },
                code=RESPONSE_CODES.success
            )

        except Exception as e:
            print("Error generating signed URL:", str(e))
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.presigned_url_error,
                data={"error": str(e)},
                code=RESPONSE_CODES.error
            )


class FilePath:
    USERS = "user"
    BUSINESS = "business"
    LEAD_QUERY = "lead_query"
    SUBSCRIPTION = "subscription"
    BLOG = "blog"
    CONTACT = "contact"
    PAYMENT = "payment_qr"
    BANNERS = "banners"
    STOCK_MEDIA = "stock_media"
    BUSINESS_BADGE = "business_badge"

    @staticmethod
    def ProfileImage():
        return f"{FilePath.USERS}/profile_image/"

    @staticmethod
    def BusinessPrimaryImage():
        return f"{FilePath.BUSINESS}/primary_image/"
    @staticmethod
    def BusinessBadge():
        return f"{FilePath.BUSINESS_BADGE}/primary_image/"

    @staticmethod
    def BusinessSecondaryImages():
        return f"{FilePath.BUSINESS}/secondary_images/"

    @staticmethod
    def LeadQueryAttachment():
        return f"{FilePath.LEAD_QUERY}/attachment/"

    @staticmethod
    def SubscriptionCover():
        return f"{FilePath.SUBSCRIPTION}/attachment/"

    @staticmethod
    def SubscriptionVideo():
        return f"{FilePath.SUBSCRIPTION}/video/"

    @staticmethod
    def SubscriptionPDF():
        return f"{FilePath.SUBSCRIPTION}/pdf/"

    @staticmethod
    def BlogCover():
        return f"{FilePath.BLOG}/cover/"

    @staticmethod
    def ContactAttachment():
        return f"{FilePath.CONTACT}/attachment/"

    @staticmethod
    def PaymentQR():
        return f"{FilePath.PAYMENT}/"

    @staticmethod
    def Banner():
        return f"{FilePath.BANNERS}/"
    @staticmethod
    def StockMedia():
        return f"{FilePath.STOCK_MEDIA}/"
