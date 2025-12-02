from app_ib.models import (
    Business,
    Location,
    BusinessBadge,
    BusinessType,
    BusinessCategory,
    BusinessSegment,
    BusinessSocialMedia,
    UserProfile,
    BusinessProfile,
    CustomUser
    )
import asyncio
from asgiref.sync import sync_to_async
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.Utils.Names import NAMES
from interior_business.Controllers.BussLocation.Tasks.BusinessLocationTasks import BUSS_LOC_TASK
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.Utils.Names import NAMES
from django.db.models import Prefetch


class BUSS_TASK:

    @classmethod
    async def UpdateBusinessBannerTask(cls, business: Business,data):
        try:
            business.bannerImageUrl = data.bannerImageUrl
            business.bannerLink = data.bannerLink
            business.bannerText = data.bannerText
            business.save()
            data = await cls.GetBusinessBannerTask(business)
            return data
        except Exception as e:
            # await MY_METHODS.printStatus(f'Error in CreateBusinessBannerTask {e}')
            return None
    
    @classmethod
    async def GetBusinessBannerTask(cls, business: Business):
        try:
            return {
                NAMES.BANNER_IMAGE_URL: business.bannerImageUrl,
                NAMES.BANNER_LINK: business.bannerLink,
                NAMES.BANNER_TEXT: business.bannerText,
            }
        except Exception as e:
            # await MY_METHODS.printStatus(f'Error in GetBusinessBannerTask {e}')
            return None

    @classmethod
    async def GetBusinessContactInfoTask(cls, business: Business):
        try:
            # 1️⃣ Fetch Business with user + user_profile + location
            business = await sync_to_async(
                lambda: Business.objects.select_related(
                    'user__user_profile',
                    NAMES.BUSINESS_LOCATION_RELATION,
                ).get(id=business.id)
            )()

            # 2️⃣ Fetch website link from BusinessSocialMedia
            website_link = await sync_to_async(
                lambda: BusinessSocialMedia.objects.filter(
                    business=business,
                    socialMedia__name__iexact=NAMES.WEBSITE
                ).values_list(NAMES.LINK, flat=True).first()
            )()

            # 3️⃣ Build location safely
            loc: Location = getattr(business, NAMES.BUSINESS_LOCATION_RELATION, None)
            if loc:
                location_parts = [
                    loc.city or NAMES.EMPTY,
                    loc.locationState.name or NAMES.EMPTY,
                    loc.locationCountry.name or NAMES.EMPTY,
                ]
                location = ', '.join([part for part in location_parts if part])
            else:
                location = NAMES.EMPTY

            # 4️⃣ Build structured response
            userProfile: UserProfile = business.user.user_profile
            data = {
                NAMES.PHONE: (
                    userProfile.phone
                    if business.user and userProfile else NAMES.EMPTY
                ),
                NAMES.COUNTRY_CODE: (
                    userProfile.countryCode
                    if business.user and userProfile else NAMES.EMPTY
                ),
                NAMES.LOCATION: location,
                NAMES.EMAIL: (
                    userProfile.email
                    if business.user and userProfile else NAMES.EMPTY
                ),
                NAMES.GMB_LINK:loc.locationLink,
                NAMES.WEBSITE_LINK: website_link or NAMES.EMPTY
            }

            return data

        except Business.DoesNotExist:
            return {NAMES.ERROR: 'Business not found'}
        except Exception as e:
            # await MY_METHODS.printStatus(f'Error in GetBusinessContactInfoTask: {e}')
            return None

    @classmethod
    async def CreateBusinessTask(cls, user_ins:CustomUser, data):
        try:
            badge = await sync_to_async(lambda: BusinessBadge.objects.filter(isDefault=True).first())()

            # Get business type (FK)
            business_type_id = getattr(data.businessType, NAMES.ID, None)
            business_type = await sync_to_async(lambda: BusinessType.objects.filter(id=business_type_id).first())()

            # Validate and fetch segments (max 5)
            segment_ids = [seg.id for seg in getattr(data, NAMES.SEGMENTS, [])]
            if len(segment_ids) > 5:
                return None  # Too many segments
            segments = await sync_to_async(lambda: list(BusinessSegment.objects.filter(id__in=segment_ids)))()
            if len(segments) != len(segment_ids):
                return None  # Invalid segment IDs

            # Validate and fetch categories (max 3)
            category_ids = [cat.id for cat in getattr(data, NAMES.CATEGORIES, [])]
            if len(category_ids) > 3:
                return None  # Too many categories
            categories = await sync_to_async(lambda: list(BusinessCategory.objects.filter(id__in=category_ids)))()
            if len(categories) != len(category_ids):
                return None  # Invalid category IDs

            # Create Business instance
            business_ins = Business()
            business_ins.user = user_ins
            business_ins.businessName = getattr(data, NAMES.BUSINESS_NAME, NAMES.EMPTY)
            business_ins.brandName = getattr(data, NAMES.BRAND_NAME, NAMES.EMPTY)
            business_ins.whatsapp = getattr(data, NAMES.WHATSAPP, NAMES.EMPTY)
            business_ins.gst = getattr(data, NAMES.GST, NAMES.EMPTY)
            business_ins.since = getattr(data, NAMES.SINCE, NAMES.EMPTY)
            business_ins.bio = getattr(data, NAMES.BIO, NAMES.EMPTY)
            business_ins.coverImageUrl = getattr(data, NAMES.COVER_IMAGE_URL, NAMES.EMPTY)
            business_ins.bannerImageUrl = getattr(data, NAMES.BANNER_IMAGE_URL, NAMES.EMPTY)
            business_ins.businessType = business_type
            business_ins.businessBadge = badge

            # Optional legacy text (store labels)
            business_ins.segment = ', '.join([s.lable for s in segments])
            business_ins.catigory = ', '.join([c.lable for c in categories])

            await sync_to_async(business_ins.save)()

            # Set M2M relations
            await sync_to_async(business_ins.businessSegment.set)(segments)
            await sync_to_async(business_ins.businessCategory.set)(categories)

            return True

        except Exception as e:
            # await MY_METHODS.printStatus(f'Error in CreateBusinessTask {e}')
            return None
    @classmethod
    async def UpdateBusinessTask(cls, business_ins:Business, data):
        try:
            # Related instances (nullable)
            loc = getattr(business_ins, NAMES.BUSINESS_LOCATION_RELATION, None)
            prof: BusinessProfile = getattr(business_ins, 'business_profile', None)

            # --- ForeignKey: BusinessType ---
            if hasattr(data, NAMES.BUSINESS_TYPE) and getattr(data.businessType, NAMES.ID, None):
                business_type = await sync_to_async(BusinessType.objects.filter(id=data.businessType.id).first)()
                if business_type:
                    business_ins.businessType = business_type

            # --- M2M: BusinessSegment (max 5) ---
            segments = getattr(data, NAMES.SEGMENTS, None)
            if isinstance(segments, list) and len(segments) <= 5:
                segment_ids = [s.id for s in segments]
                segment_objs = await sync_to_async(lambda: list(BusinessSegment.objects.filter(id__in=segment_ids)))()
                if len(segment_objs) == len(segment_ids):
                    await sync_to_async(business_ins.businessSegment.set)(segment_objs)
                    business_ins.segment = ', '.join([s.lable for s in segment_objs])  # legacy

            # --- M2M: BusinessCategory (max 3) ---
            categories = getattr(data, NAMES.CATEGORIES, None)
            if isinstance(categories, list) and len(categories) <= 3:
                category_ids = [c.id for c in categories]
                category_objs = await sync_to_async(lambda: list(BusinessCategory.objects.filter(id__in=category_ids)))()
                if len(category_objs) == len(category_ids):
                    await sync_to_async(business_ins.businessCategory.set)(category_objs)
                    business_ins.catigory = ', '.join([c.lable for c in category_objs])  # legacy

            # --- Simple Fields ---
            business_ins.businessName = getattr(data, NAMES.BUSINESS_NAME, business_ins.businessName)
            business_ins.brandName = getattr(data, NAMES.BRAND_NAME, business_ins.brandName)
            business_ins.gst = getattr(data, NAMES.GST, business_ins.gst)
            business_ins.since = getattr(data, NAMES.SINCE, business_ins.since)
            business_ins.bio = getattr(data, NAMES.BIO, business_ins.bio)
            business_ins.coverImageUrl = getattr(data, NAMES.COVER_IMAGE_URL, business_ins.coverImageUrl)
            business_ins.bannerImageUrl = getattr(data, NAMES.BANNER_IMAGE_URL, business_ins.bannerImageUrl)
            await sync_to_async(business_ins.save)()

            # --- Business Location (if exists) ---
            if loc:
                await BUSS_LOC_TASK.UpdateBusinessLocTask(loc, data)
            else:
                await BUSS_LOC_TASK.CreateBusinessLocTask(business_ins, data)

            # --- Business Profile (if exists) ---
            if prof and hasattr(data, NAMES.YOUTUBE_LINK):
                prof.youtubeLink = getattr(data, NAMES.YOUTUBE_LINK)
                await sync_to_async(prof.save)()

            return await cls.GetBusinessInfo(business_ins.id)

        except Exception as e:
            # await MY_METHODS.printStatus(f'Error in UpdateBusinessTask: {e}')
            return None

    @classmethod
    async def GetBusinessInfo(cls, id):
        try:
            business_ins = await sync_to_async(Business.objects.get)(pk=id)
            business_loc_ins:Location = getattr(business_ins, NAMES.BUSINESS_LOCATION_RELATION, None)
            business_prof_ins: BusinessProfile = getattr(business_ins, 'business_profile', None)

            # Get related segments and categories (as objects)
            segments = await sync_to_async(lambda: list(business_ins.businessSegment.all()))()
            categories = await sync_to_async(lambda: list(business_ins.businessCategory.all()))()

            # Serialize them
            segment_data = [await cls.GetBusinessTypeData(seg) for seg in segments]
            category_data = [await cls.GetBusinessTypeData(cat) for cat in categories]
            # await MY_METHODS.printStatus(f'category {category_data},categories {categories}')

            data = {
                NAMES.BUSINESS_NAME: business_ins.businessName,
                NAMES.BRAND_NAME: business_ins.brandName,
                NAMES.SEGMENTS: segment_data,
                NAMES.CATEGORIES: category_data,
                NAMES.WHATSAPP: business_ins.whatsapp,
                NAMES.GST: business_ins.gst,
                NAMES.COVER_IMAGE_URL: business_ins.coverImageUrl if business_ins.coverImageUrl else NAMES.EMPTY,
                NAMES.BANNER_IMAGE_URL: business_ins.bannerImageUrl if business_ins.bannerImageUrl else NAMES.EMPTY,
                NAMES.SINCE: business_ins.since,
                NAMES.ID: business_ins.id,
                NAMES.BIO: business_ins.bio,
                NAMES.UPDATED_AT: business_ins.updatedAt,
                NAMES.BADGE: business_ins.businessBadge.imageUrl if business_ins.businessBadge else None,
                NAMES.TIMESTAMP: business_ins.timestamp
            }

            rating = await MY_METHODS.get_random_rating()
            data[NAMES.RATING] = f'{rating}'
            data[NAMES.RATING_VALUE] = float(rating)

            # Serialize business type
            if business_ins.businessType:
                data[NAMES.BUSINESS_TYPE] = await cls.GetBusinessTypeData(business_ins.businessType)

            # Location
            if business_loc_ins:
                location = await BUSS_LOC_TASK.GetBusinessLocTask(business_loc_ins)
                data[NAMES.GMB_LINK] = location[NAMES.GMB_LINK]
                data[NAMES.PINCODE] =location[NAMES.PINCODE]
                data[NAMES.CITY] = location[NAMES.CITY]
                data[NAMES.STATE] = location[NAMES.STATE]
                data[NAMES.COUNTRY] = location[NAMES.COUNTRY]

            # Profile
            if business_prof_ins:
                data[NAMES.YOUTUBE_LINK] = business_prof_ins.youtubeLink

            return data

        except Exception as e:
            # await MY_METHODS.printStatus(f'Error in GetBusinessInfo: {e}')
            return None

    @classmethod
    async def GetBusinessInfoForSearch(cls, id):
        try:
            business_ins = await sync_to_async(
                Business.objects.select_related('business_profile', 'business_type')
                .prefetch_related('businessSegment', 'businessCategory')
                .get
            )(pk=id)

            # Business profile image
            business_profile: BusinessProfile = getattr(business_ins, 'business_profile', None)
            business_image = business_profile.primaryImageUrl if business_profile else None

            # Segments
            segments = await sync_to_async(lambda: list(business_ins.businessSegment.all()))()
            segment_data = [await cls.GetBusinessTypeData(seg) for seg in segments]

            # Categories
            categories = await sync_to_async(lambda: list(business_ins.businessCategory.all()))()
            category_data = [await cls.GetBusinessTypeData(cat) for cat in categories]

            # Business Type
            business_type_data = None
            if business_ins.businessType:
                business_type_data = await cls.GetBusinessTypeData(business_ins.businessType)

            # Final response
            data = {
                NAMES.ID: business_ins.id,
                NAMES.BUSINESS_NAME: business_ins.businessName,
                NAMES.BRAND_NAME: business_ins.brandName,
                NAMES.COVER_IMAGE_URL: business_ins.coverImageUrl,
                NAMES.SINCE: business_ins.since,
                NAMES.BUSINESS_IMAGE: business_image,
                NAMES.SEGMENTS: segment_data,
                NAMES.CATEGORIES: category_data,
                NAMES.BUSINESS_TYPE: business_type_data,
            }

            return data

        except Exception as e:
            # await MY_METHODS.printStatus(f'Error in GetBusinessInfoForSearch: {e}')
            return None

    @classmethod
    async def GetBusinessTypeData(cls,businesstype:BusinessCategory):
        try:
            randomNumber = await MY_METHODS.getRandomNumber()
            
            sqUrl= businesstype.imageSQUrl or NAMES.RANDOM_SQ_IMAGE.replace('{num}', randomNumber)
            rtUrl = businesstype.imageRTUrl or NAMES.RANDOM_RT_IMAGE.replace('{num}', randomNumber)
            

            typeData={
                NAMES.ID: businesstype.id,
                NAMES.LABEL: businesstype.lable,
                NAMES.VALUE: businesstype.value,
                NAMES.IMAGE_SQ_URL: sqUrl,
                NAMES.IMAGE_RT_URL: rtUrl
            }

            return typeData
        except Exception as e:
            # await MY_METHODS.printStatus(f'Error in GetAllBusinessTypes: {e}')
            return None
    @classmethod
    async def GetBusinessSegmentData(cls,businesstype:BusinessSegment):
        try:
            randomNumber = await MY_METHODS.getRandomNumber()
            business:Business = businesstype.business_segment.first()
            if not business:
                sqUrl= businesstype.imageSQUrl or NAMES.RANDOM_SQ_IMAGE.replace('{num}', randomNumber)
                rtUrl = businesstype.imageRTUrl or NAMES.RANDOM_RT_IMAGE.replace('{num}', randomNumber)
            else:
                sqUrl = business.coverImageUrl or businesstype.imageSQUrl or NAMES.RANDOM_SQ_IMAGE.replace('{num}', randomNumber)
                rtUrl =  business.bannerImageUrl or businesstype.imageRTUrl or NAMES.RANDOM_RT_IMAGE.replace('{num}', randomNumber)

            typeData={
                NAMES.ID: businesstype.id,
                NAMES.LABEL: businesstype.lable,
                NAMES.VALUE: businesstype.value,
                NAMES.IMAGE_SQ_URL: sqUrl,
                NAMES.IMAGE_RT_URL: rtUrl
            }

            return typeData
        except Exception as e:
            # await MY_METHODS.printStatus(f'Error in GetAllBusinessTypes: {e}')
            return None