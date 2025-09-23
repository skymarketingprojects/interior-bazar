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

            FolderPath =FilePath.get_path(ImageIntent)
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
    PATHS = {
        "ProfileImage": "user/profile_image/",
        "BusinessCover": "business/cover/",
        "BusinessPrimaryImage": "business/primary_image/",
        "BusinessBadge": "business_badge/primary_image/",
        "BusinessSecondaryImages": "business/secondary_images/",
        "LeadQueryAttachment": "lead_query/attachment/",
        "SubscriptionCover": "subscription/attachment/",
        "SubscriptionVideo": "subscription/video/",
        "SubscriptionPDF": "subscription/pdf/",
        "BlogCover": "blog/cover/",
        "ContactAttachment": "contact/attachment/",
        "PaymentQR": "payment_qr/",
        "Banner": "banners/",
        "StockMedia": "stock_media/",
        "PaymentScreenshot": "payment_screenshot/",
    }

    @classmethod
    def get_path(cls, intent_name):
        path = cls.PATHS.get(intent_name)
        if not path:
            raise ValueError(f"Unsupported ImageIntent: {intent_name}")
        return path
