from asgiref.sync import sync_to_async
from app_ib.models import (
    BusinessProfile,
    Business,
    BusinessSocialMedia,
    Location,
    UserProfile
    )
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.Utils.Names import NAMES

import asyncio
class BUSS_PROF_TASK:

    @classmethod
    async def GetBusinessProfileTask(cls, business_id: int):
        try:
            # 1️⃣ Fetch Business + User + UserProfile in one optimized query
            business = await sync_to_async(
                lambda: Business.objects.select_related(
                    'user__user_profile'
                ).only(
                    NAMES.ID,
                    NAMES.BUSINESS_NAME,
                    'bannerImageUrl',
                    'user__id',
                    'user__user_profile__phone',
                    'user__user_profile__countryCode',
                    'user__user_profile__profileImageUrl',
                ).get(id=business_id)
            )()
            # 2️⃣ Fetch Social Media (with related social media names)
            social_media_data = await sync_to_async(
                lambda: list(
                    BusinessSocialMedia.objects.filter(business=business)
                    .select_related(NAMES.SOCIAL_MEDIA)
                    .values('socialMedia__name', NAMES.LINK)
                )
            )()

            # 3️⃣ Build Response
            profile: UserProfile = business.user.user_profile
            response_data = {
                NAMES.BANNER_IMAGE_URL: business.bannerImageUrl or NAMES.EMPTY,
                NAMES.PROFILE_IMAGE_URL: (
                    profile.profileImageUrl
                    if business.user and business.user.user_profile
                    else NAMES.EMPTY
                ),
                NAMES.PHONE: (
                    profile.phone
                    if business.user and profile
                    else NAMES.EMPTY
                ),
                NAMES.COUNTRY_CODE: (
                    profile.countryCode
                    if business.user and profile
                    else '0'
                ),
                NAMES.BUSINESS_NAME: business.businessName,
                NAMES.SOCIAL_MEDIA:{f"{sm['socialMedia__name']}Link": sm[NAMES.LINK] for sm in social_media_data},
            }

            return response_data

        except Business.DoesNotExist:
            return {NAMES.ERROR: 'Business not found'}
        except Exception as e:
            print('Error in GetBusinessProfile:', e)
            return {NAMES.ERROR: str(e)}

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
                NAMES.ID:business_prof_ins.pk,
            }
            return business_prof_data
            
        except Exception as e:
            # await MY_METHODS.printStatus(f'Error in GetBusinessProfTask {e}')
            return None