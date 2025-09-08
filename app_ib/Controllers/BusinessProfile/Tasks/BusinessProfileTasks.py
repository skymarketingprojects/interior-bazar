from asgiref.sync import sync_to_async
from app_ib.models import BusinessProfile, Business

class BUSS_PROF_TASK:

    @classmethod
    async def CreateBusinessProfileTask(self, business_ins, data):
        try:
            business_prof_ins = BusinessProfile()
            business_prof_ins.business= business_ins
            business_prof_ins.about= data.about
            business_prof_ins.youtube_link= data.youtube_link
            business_prof_ins.primary_image_url= data.primary_image_url if data.primary_image_url else ''
            business_prof_ins.secondary_images_url= data.secondary_images_url if data.secondary_images_url else ''
            await sync_to_async(business_prof_ins.save)()
            return True
            
        except Exception as e:
            print(f'Error in CreateBusinessProfileTask {e}')
            return None

    @classmethod
    async def UpdateBusinessProfileTask(self, business_prof_ins, data):
        try:
            business_prof_ins.about= data.about
            business_prof_ins.youtube_link= data.youtube_link
            business_prof_ins.primary_image_url= data.primary_image_url if data.primary_image_url else business_prof_ins.primary_image_url
            business_prof_ins.secondary_images_url= data.secondary_images_url if data.secondary_images_url else business_prof_ins.secondary_images_url
            await sync_to_async(business_prof_ins.save)()
            return True
            
        except Exception as e:
            print(f'Error in UpdateBusinessProfileTask {e}')
            return None


    @classmethod
    async def GetBusinessProfTask(self,business_prof_ins):
        try:
            business_prof_data={
                'about':business_prof_ins.about,
                'youtube_link':business_prof_ins.youtube_link,
                'id':business_prof_ins.pk,
            }
            return business_prof_data
            
        except Exception as e:
            print(f'Error in GetBusinessProfTask {e}')
            return None