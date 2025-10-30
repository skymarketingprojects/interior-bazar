from asgiref.sync import sync_to_async
from app_ib.models import BusinessProfile, Business, BusinessSocialMedia
from app_ib.Utils.MyMethods import MY_METHODS
class BUSS_PROF_TASK:

    @classmethod
    async def GetBusinessProfileTask(cls, business_id: int):
        try:
            # 1️⃣ Fetch Business + User + UserProfile in one optimized query
            business = await sync_to_async(
                lambda: Business.objects.select_related(
                    "user__user_profile"
                ).only(
                    "id",
                    "business_name",
                    "banner_image_url",
                    "user__id",
                    "user__user_profile__phone",
                    "user__user_profile__countryCode",
                    "user__user_profile__profile_image_url",
                ).get(id=business_id)
            )()
            businessLocation = business.business_location
            # 2️⃣ Fetch Social Media (with related social media names)
            social_media_data = await sync_to_async(
                lambda: list(
                    BusinessSocialMedia.objects.filter(business=business)
                    .select_related("socialMedia")
                    .values("socialMedia__name", "link")
                )
            )()

            # 3️⃣ Build Response
            response_data = {
                "bannerImageUrl": business.banner_image_url or "",
                "profile_image_url": (
                    business.user.user_profile.profile_image_url
                    if business.user and business.user.user_profile
                    else ""
                ),
                "phone": (
                    business.user.user_profile.phone
                    if business.user and business.user.user_profile
                    else ""
                ),
                "countryCode": (
                    business.user.user_profile.countryCode
                    if business.user and business.user.user_profile
                    else "0"
                ),
                "businessName": business.business_name,
                "socialMedia":{f"{sm['socialMedia__name']}Link": sm["link"] for sm in social_media_data},
            }

            return response_data

        except Business.DoesNotExist:
            return {"error": "Business not found"}
        except Exception as e:
            print("Error in GetBusinessProfile:", e)
            return {"error": str(e)}

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
            #await MY_METHODS.printStatus(f'Error in CreateBusinessProfileTask {e}')
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
            #await MY_METHODS.printStatus(f'Error in UpdateBusinessProfileTask {e}')
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
            #await MY_METHODS.printStatus(f'Error in GetBusinessProfTask {e}')
            return None