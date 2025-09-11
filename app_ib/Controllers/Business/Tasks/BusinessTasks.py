from app_ib.models import Business,Location,BusinessBadge
from asgiref.sync import sync_to_async
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.LocalResponse import LocalResponse

class BUSS_TASK:

    @classmethod
    async def CreateBusinessTask(self, user_ins, data):
        try:
            badge = await sync_to_async(lambda: BusinessBadge.objects.filter(isDefault=True).first())()
            business_ins = Business()
            business_ins.user=user_ins
            business_ins.business_name=getattr(data, 'business_name', "")
            business_ins.segment=getattr(data, 'segment', "")
            business_ins.catigory=getattr(data, 'category', "")
            business_ins.whatsapp = getattr(data, 'whatsapp', "")
            business_ins.gst = getattr(data, 'gst', "")
            business_ins.since = getattr(data, 'since',"" )
            business_ins.bio = getattr(data, 'bio', "")
            business_ins.businessBadge = badge
            await sync_to_async(business_ins.save)()
            return True
            
        except Exception as e:
            print(f'Error in CreateBusinessTask {e}')
            return None


    @classmethod
    async def UpdateBusinessTask(self, business_ins, data):
        try:
            business_loc_ins = business_ins.business_location if hasattr(business_ins, 'business_location') else None
            business_prof_ins =business_ins.business_profile if hasattr(business_ins, 'business_profile') else None

            business_ins.business_name=getattr(data, 'business_name', business_ins.business_name)
            business_ins.segment=getattr(data, 'segment', business_ins.segment)
            business_ins.catigory=getattr(data, 'category', business_ins.catigory)
            business_ins.whatsapp = getattr(data, 'whatsapp', business_ins.whatsapp)
            business_ins.gst = getattr(data, 'gst', business_ins.gst)
            business_ins.since = getattr(data, 'since', business_ins.since)
            business_ins.bio = getattr(data, 'bio', business_ins.bio)
            business_ins.cover_image_url = getattr(data, 'cover_image_url', business_ins.cover_image_url)
            await sync_to_async(business_ins.save)()

            if business_loc_ins:
                business_loc_ins.pin_code= getattr(data, 'pin_code', business_loc_ins.pin_code) if business_loc_ins else None
                business_loc_ins.city= getattr(data, 'city', business_loc_ins.city) if business_loc_ins else None
                business_loc_ins.state= getattr(data, 'state', business_loc_ins.state) if business_loc_ins else None
                business_loc_ins.country= getattr(data, 'country', business_loc_ins.country) if business_loc_ins else None
                business_loc_ins.location_link= getattr(data, 'location_link', business_loc_ins.location_link   ) if business_loc_ins else None
                await sync_to_async(business_loc_ins.save)()
            
            if business_prof_ins:
                business_prof_ins.youtube_link= getattr(data, 'youtube_link', business_prof_ins.youtube_link) if business_prof_ins else None
                await sync_to_async(business_prof_ins.save)()
            return True
            
        except Exception as e:
            print(f'Error in UpdateBusinessTask {e}')
            return None


    @classmethod
    async def GetBusinessInfo(self,id):
        try:
            business_ins = await sync_to_async(Business.objects.get)(pk=id)
            business_loc_ins = business_ins.business_location if hasattr(business_ins, 'business_location') else None
            business_prof_ins =business_ins.business_profile if hasattr(business_ins, 'business_profile') else None
            print(f'business_loc_ins {business_loc_ins}')

            data = {
                'business_name': business_ins.business_name,
                'segment': business_ins.segment,
                'category': business_ins.catigory,
                'whatsapp': business_ins.whatsapp,
                'gst': business_ins.gst,
                'cover_image_url': business_ins.cover_image_url,
                'since': business_ins.since,
                'buss_id': business_ins.id,
                'bio': business_ins.bio,
                'updated_at': business_ins.updated_at,
                'badge': business_ins.businessBadge.image_url if business_ins.badge else None,
                # 'pin_code':business_loc_ins.pin_code,
                # 'city':business_loc_ins.city,
                # 'state':business_loc_ins.state,
                # 'country':business_loc_ins.country,
                # 'location_link':business_loc_ins.location_link,
            }
            if business_loc_ins is not None:
                data['location_link']= business_loc_ins.location_link
                data['pin_code']= business_loc_ins.pin_code
                data['city']= business_loc_ins.city
                data['state']= business_loc_ins.state
                data['country']= business_loc_ins.country
            if business_prof_ins:
                data['youtube_link']= business_prof_ins.youtube_link
            return data
            
        except Exception as e:
            print(f'Error in GetBusinessInfo {e}')
            return None