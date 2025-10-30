from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.models import BusinessSocialMedia, SocialMedia
from interior_business.Controllers.BusinessSocialMedia.Tasks.BusinessSocialMediaTasks import BSM_TASK
from asgiref.sync import sync_to_async
from app_ib.models import Business
class BSM_CONTROLLER:
    
    @classmethod
    async def CreateBusinessSocialMedia(cls, data,business:Business):
        try:
            bsm = None
            exist = await sync_to_async(BusinessSocialMedia.objects.filter(business=business).exists)()
            if exist:
                bsm_list = await sync_to_async(list)(
                    BusinessSocialMedia.objects.filter(business=business)
                )

                bsm = await BSM_TASK.UpdateBusinessSocialMedia(bsm_list, data)
            else:
                bsm = await BSM_TASK.CreateBusinessSocialMedia(data,business)
            return LocalResponse(
                code=RESPONSE_CODES.success,
                response=RESPONSE_MESSAGES.success,
                message="Business Social Media created successfully",
                data=bsm
            )
        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                code=RESPONSE_CODES.error,
                message=str(e),
                data={}
            )

    @classmethod
    async def UpdateBusinessSocialMedia(cls, business: Business, data: dict):
        try:
            bsm_list = await sync_to_async(list)(
                BusinessSocialMedia.objects.filter(business=business)
            )

            updated_bsms = await BSM_TASK.UpdateBusinessSocialMedia(bsm_list, data)

            return LocalResponse(
                code=RESPONSE_CODES.success,
                response=RESPONSE_MESSAGES.success,
                message="Business Social Media updated successfully",
                data=updated_bsms
            )

        except Exception as e:
            print("Error in UpdateBusinessSocialMedia:", e)
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                code=RESPONSE_CODES.error,
                message=str(e),
                data={}
            )

    @classmethod
    async def DeleteBusinessSocialMedia(cls, business):
        try:
            result = await BSM_TASK.DeleteBusinessSocialMedia(business)
            return LocalResponse(
                code=RESPONSE_CODES.success,
                response=RESPONSE_MESSAGES.success,
                message="Business Social Media deleted successfully",
                data={'deleted': result}
            )
        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                code=RESPONSE_CODES.error,
                message=str(e),
                data={}
            )

    @classmethod
    async def GetBusinessSocialMedia(cls, business):
        try:
            data = await BSM_TASK.GetBusinessSocialMediaByBusiness(business)
            return LocalResponse(
                code=RESPONSE_CODES.success,
                response=RESPONSE_MESSAGES.success,
                message="Fetched Business Social Media successfully",
                data=data
            )
        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                code=RESPONSE_CODES.error,
                message=str(e),
                data={}
            )

    @classmethod
    async def GetSocialMediaList(cls):
        try:
            data = await BSM_TASK.GetSocialMediaList()
            return LocalResponse(
                code=RESPONSE_CODES.success,
                response=RESPONSE_MESSAGES.success,
                message="Fetched Social Media list successfully",
                data=data
            )
        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                code=RESPONSE_CODES.error,
                message=str(e),
                data={}
            )
