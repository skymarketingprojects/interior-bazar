from app_ib.models import BusinessSocialMedia, SocialMedia, Business
from asgiref.sync import sync_to_async

class BSM_TASK:

    @classmethod
    async def CreateBusinessSocialMedia(cls, data: dict, business: Business):
        try:
            created_bsms = []
            for key, link in data.items():
                if not key.endswith("Link"):
                    continue

                # Strip "Link" and normalize name
                sm_name = key.replace("Link", "").strip().lower()

                # Get or create SocialMedia
                social_media, created = await sync_to_async(SocialMedia.objects.get_or_create)(
                    name=sm_name
                )

                # Create BusinessSocialMedia
                bsm = BusinessSocialMedia(
                    business=business,
                    socialMedia=social_media,
                    link=link
                )
                await sync_to_async(bsm.save)()
                created_bsms.append(await cls.GetBusinessSocialMedia(bsm))
            
            data = await cls.GetBusinessSocialMediaByBusiness(business)

            return data

        except Exception as e:
            return False

    @classmethod
    async def UpdateBusinessSocialMedia(cls, bsm_list:list[BusinessSocialMedia], data):
        try:
            business = bsm_list[0].business

            for bsm in bsm_list:
                sm_name = bsm.socialMedia.name.lower()
                key = f"{sm_name}Link"

                if key in data:
                    bsm.link = data[key]
                    await sync_to_async(bsm.save)()
                else:
                    social_media, created = await sync_to_async(SocialMedia.objects.get_or_create)(
                        name=sm_name
                    )
                    bsm = BusinessSocialMedia(
                        business=business,
                        socialMedia=social_media,
                        link=data[key]
                    )
                    await sync_to_async(bsm.save)()
            data = await cls.GetBusinessSocialMediaByBusiness(bsm_list[0].business)
            return data
        except Exception as e:
            return False

    @classmethod
    async def DeleteBusinessSocialMedia(cls, business):
        try:
            bsm_list = await sync_to_async(list)(BusinessSocialMedia.objects.filter(business=business))
            for bsm in bsm_list:
                await sync_to_async(bsm.delete)()
            return True
        except Exception as e:
            return False

    @classmethod
    async def GetBusinessSocialMediaByBusiness(cls, business:Business):
        try:
            bsm_list = await sync_to_async(list)(BusinessSocialMedia.objects.filter(business=business))
            data ={f"{bsm.socialMedia.name.lower()}Link": bsm.link for bsm in bsm_list}
            return data
        except Exception as e:
            return False

    @classmethod
    async def GetSocialMediaList(cls):
        try:
            sm_list = await sync_to_async(list)(SocialMedia.objects.all())
            return [{'id': sm.id, 'name': sm.name} for sm in sm_list]
        except Exception as e:
            return False
    
    @classmethod
    async def GetBusinessSocialMedia(cls, bsm:BusinessSocialMedia):
        try:

            return {
                'id': bsm.id,
                'business': bsm.business.id,
                'socialMedia': bsm.socialMedia.name,
                'link': bsm.link
            }
        except Exception as e:
            return False
