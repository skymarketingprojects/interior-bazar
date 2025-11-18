from asgiref.sync import sync_to_async
from app_ib.models import BusinessProfile, Business
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.Utils.Names import NAMES

class BUSS_PROF_TASK:

    @classmethod
    async def CreateBusinessProfileTask(self, business_ins, data):
        try:
            business_prof_ins = BusinessProfile()
            business_prof_ins.business= business_ins
            business_prof_ins.about= data.about
            business_prof_ins.youtubeLink= data.youtubeLink
            business_prof_ins.primaryImageUrl= data.primaryImageUrl if data.primaryImageUrl else NAMES.EMPTY
            business_prof_ins.secondaryImagesUrl= data.secondaryImagesUrl if data.secondaryImagesUrl else NAMES.EMPTY
            await sync_to_async(business_prof_ins.save)()
            return True
            
        except Exception as e:
            # await MY_METHODS.printStatus(f'Error in CreateBusinessProfileTask {e}')
            return None

    @classmethod
    async def UpdateBusinessProfileTask(self, business_prof_ins:BusinessProfile, data):
        try:
            business_prof_ins.about= data.about
            business_prof_ins.youtubeLink= data.youtubeLink
            business_prof_ins.primaryImageUrl= data.primaryImageUrl if data.primaryImageUrl else business_prof_ins.primaryImageUrl
            business_prof_ins.secondaryImagesUrl= data.secondaryImagesUrl if data.secondaryImagesUrl else business_prof_ins.secondaryImagesUrl
            await sync_to_async(business_prof_ins.save)()
            return True
            
        except Exception as e:
            # await MY_METHODS.printStatus(f'Error in UpdateBusinessProfileTask {e}')
            return None


    @classmethod
    async def GetBusinessProfTask(self,business_prof_ins:BusinessProfile):
        try:
            business_prof_data={
                NAMES.ABOUT:business_prof_ins.about,
                NAMES.YOUTUBE_LINK:business_prof_ins.youtubeLink,
                NAMES.PRIMARY_IMAGE_URL:business_prof_ins.primaryImageUrl,
                NAMES.SECONDARY_IMAGES_URL:business_prof_ins.secondaryImagesUrl,
                NAMES.ID:business_prof_ins.pk
            }
            return business_prof_data
            
        except Exception as e:
            # await MY_METHODS.printStatus(f'Error in GetBusinessProfTask {e}')
            return None