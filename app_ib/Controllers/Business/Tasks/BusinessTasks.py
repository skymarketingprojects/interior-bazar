from app_ib.models import Business, Location, BusinessBadge, BusinessType, BusinessCategory, BusinessSegment, BusinessProfile
import asyncio
from asgiref.sync import sync_to_async
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.Names import NAMES
from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.Controllers.BussLocation.Tasks.BusinessLocationTasks import BUSS_LOC_TASK
from app_ib.Utils.MyMethods import MY_METHODS
from django.db.models import Prefetch

from app_ib.models import BusinessSegment, CustomUser

class BUSS_TASK:
    @classmethod
    async def CreateBusinessTask(cls, user_ins: CustomUser, data):
        try:
            badge = await sync_to_async(lambda: BusinessBadge.objects.filter(isDefault=True).first())()
            business_type_id = getattr(data.businessType, NAMES.ID, None)
            business_type = await sync_to_async(lambda: BusinessType.objects.filter(id=business_type_id).first())()

            segment_ids = [seg.id for seg in getattr(data, NAMES.SEGMENTS, [])]
            if len(segment_ids) > 5: return None
            segments = await sync_to_async(lambda: list(BusinessSegment.objects.filter(id__in=segment_ids)))()
            if len(segments) != len(segment_ids): return None

            category_ids = [cat.id for cat in getattr(data, NAMES.CATEGORIES, [])]
            if len(category_ids) > 3: return None
            categories = await sync_to_async(lambda: list(BusinessCategory.objects.filter(id__in=category_ids)))()
            if len(categories) != len(category_ids): return None

            business_ins = Business()
            business_ins.user = user_ins
            business_ins.businessName = getattr(data, NAMES.BUSINESS_NAME, NAMES.EMPTY)
            business_ins.whatsapp = getattr(data, NAMES.WHATSAPP, NAMES.EMPTY)
            business_ins.gst = getattr(data, NAMES.GST, NAMES.EMPTY)
            business_ins.since = getattr(data, NAMES.SINCE, NAMES.EMPTY)
            business_ins.bio = getattr(data, NAMES.BIO, NAMES.EMPTY)
            business_ins.bannerImageUrl = getattr(data, NAMES.BANNER_IMAGE_URL, NAMES.EMPTY)
            business_ins.bannerLink = getattr(data, NAMES.BANNER_LINK, NAMES.EMPTY)
            business_ins.bannerText = getattr(data, NAMES.BANNER_TEXT, NAMES.EMPTY)
            business_ins.coverImageUrl = getattr(data, NAMES.COVER_IMAGE_URL, NAMES.EMPTY)
            business_ins.businessType = business_type
            business_ins.businessBadge = badge

            await sync_to_async(business_ins.save)()
            await sync_to_async(business_ins.businessSegment.set)(segments)
            await sync_to_async(business_ins.businessCategory.set)(categories)

            return True
        except Exception as e:
            return None

    @classmethod
    async def UpdateBusinessTask(cls, business_ins: Business, data):
        try:
            loc = getattr(business_ins, NAMES.BUSINESS_LOCATION, None)
            prof = getattr(business_ins, NAMES.BUSINESS_PROFILE, None)

            if hasattr(data, NAMES.BUSINESS_TYPE) and getattr(data.businessType, NAMES.ID, None):
                business_type = await sync_to_async(BusinessType.objects.filter(id=data.businessType.id).first)()
                if business_type: business_ins.businessType = business_type

            segments = getattr(data, NAMES.SEGMENTS, None)
            if isinstance(segments, list) and len(segments) <= 5:
                segment_ids = [s.id for s in segments]
                segment_objs = await sync_to_async(lambda: list(BusinessSegment.objects.filter(id__in=segment_ids)))()
                if len(segment_objs) == len(segment_ids):
                    await sync_to_async(business_ins.businessSegment.set)(segment_objs)

            categories = getattr(data, NAMES.CATEGORIES, None)
            if isinstance(categories, list) and len(categories) <= 3:
                category_ids = [c.id for c in categories]
                category_objs = await sync_to_async(lambda: list(BusinessCategory.objects.filter(id__in=category_ids)))()
                if len(category_objs) == len(category_ids):
                    await sync_to_async(business_ins.businessCategory.set)(category_objs)

            business_ins.businessName = getattr(data, NAMES.BUSINESS_NAME, business_ins.businessName)
            business_ins.gst = getattr(data, NAMES.GST, business_ins.gst)
            business_ins.since = getattr(data, NAMES.SINCE, business_ins.since)
            business_ins.bio = getattr(data, NAMES.BIO, business_ins.bio)
            business_ins.bannerImageUrl = getattr(data, NAMES.BANNER_IMAGE_URL, business_ins.bannerImageUrl)
            business_ins.bannerLink = getattr(data, NAMES.BANNER_LINK, business_ins.bannerLink)
            business_ins.bannerText = getattr(data, NAMES.BANNER_TEXT, business_ins.bannerText)
            business_ins.coverImageUrl = getattr(data, NAMES.COVER_IMAGE_URL, business_ins.coverImageUrl)
            await sync_to_async(business_ins.save)()

            if loc: await BUSS_LOC_TASK.UpdateBusinessLocTask(loc, data)
            else: await BUSS_LOC_TASK.CreateBusinessLocTask(business_ins, data)

            if prof and hasattr(data, NAMES.YOUTUBELINK):
                prof.youtubeLink = getattr(data, NAMES.YOUTUBELINK)
                await sync_to_async(prof.save)()

            return await cls.GetBusinessInfo(business_ins.id)
        except Exception as e:
            return None

    @classmethod
    async def BulkSerializeBusinessInfo(cls, business_list):
        """
        High-performance bulk serialization for Business instances.
        Maintains EXACT legacy output format.
        """
        results = []
        for business in business_list:
            try:
                # 1. Relations
                loc_ins = getattr(business, 'business_location', None)
                prof_ins = getattr(business, 'business_profile', None)
                
                # 2. M2Ms (already pre-fetched in the list)
                segments = list(business.businessSegment.all())
                categories = list(business.businessCategory.all())
                
                segment_data = [cls.GetBusinessTypeDataSync(seg) for seg in segments]
                category_data = [cls.GetBusinessTypeDataSync(cat) for cat in categories]

                data = {
                    NAMES.BUSINESS_NAME: business.businessName,
                    NAMES.SEGMENTS: segment_data,
                    NAMES.CATEGORIES: category_data,
                    NAMES.WHATSAPP: business.whatsapp,
                    NAMES.GST: business.gst,
                    NAMES.COVER_IMAGE_URL: business.coverImageUrl,
                    NAMES.SINCE: business.since,
                    NAMES.ID: business.id,
                    NAMES.BIO: business.bio,
                    NAMES.UPDATED_AT: business.updatedAt,
                    NAMES.BADGE: business.businessBadge.imageUrl if business.businessBadge else None,
                    NAMES.TIMESTAMP: business.timestamp
                }

                if business.businessType:
                    data[NAMES.BUSINESS_TYPE] = cls.GetBusinessTypeDataSync(business.businessType)

                if loc_ins:
                    state_data = {NAMES.ID: loc_ins.locationState.id, NAMES.NAME: loc_ins.locationState.name} if loc_ins.locationState else None
                    country_data = {NAMES.ID: loc_ins.locationCountry.id, NAMES.NAME: loc_ins.locationCountry.code} if loc_ins.locationCountry else None
                    
                    data[NAMES.LOCATION_LINK] = loc_ins.locationLink
                    data[NAMES.PINCODE] = loc_ins.pinCode
                    data[NAMES.CITY] = loc_ins.city
                    data[NAMES.STATE] = state_data
                    data[NAMES.COUNTRY] = country_data

                if prof_ins:
                    data[NAMES.YOUTUBE_LINK] = prof_ins.youtubeLink

                results.append(data)
            except: pass
        return results

    @classmethod
    async def GetBusinessInfo(cls, id):
        """
        Optimized single fetch with pre-fetching.
        """
        try:
            queryset = Business.objects.filter(pk=id).select_related(
                'business_location', 'business_location__locationState', 
                'business_location__locationCountry', 'business_profile',
                'businessBadge', 'businessType'
            ).prefetch_related('businessSegment', 'businessCategory')
            
            business_list = await sync_to_async(list)(queryset)
            data_list = await cls.BulkSerializeBusinessInfo(business_list)
            return data_list[0] if data_list else None
        except Exception as e:
            return None

    @classmethod
    async def GetBusinessInfoForSearch(cls, id):
        """
        Maintains legacy search serialization but uses optimized fetch.
        """
        try:
            queryset = Business.objects.filter(pk=id).select_related(
                'businessType', 'business_profile'
            ).prefetch_related('businessSegment', 'businessCategory')
            
            business_ins = await sync_to_async(queryset.get)()
            business_profile = getattr(business_ins, 'business_profile', None)
            business_image = business_profile.primaryImageUrl if business_profile else None

            segment_data = [cls.GetBusinessTypeDataSync(seg) for seg in business_ins.businessSegment.all()]
            category_data = [cls.GetBusinessTypeDataSync(cat) for cat in business_ins.businessCategory.all()]

            data = {
                NAMES.ID: business_ins.id,
                NAMES.BUSINESS_NAME: business_ins.businessName,
                NAMES.COVER_IMAGE_URL: business_ins.coverImageUrl,
                NAMES.SINCE: business_ins.since,
                NAMES.BUSINESS_IMAGE: business_image,
                NAMES.SEGMENTS: segment_data,
                NAMES.CATEGORIES: category_data,
                NAMES.BUSINESS_TYPE: cls.GetBusinessTypeDataSync(business_ins.businessType) if business_ins.businessType else None,
            }
            return data
        except: return None

    @staticmethod
    def GetBusinessTypeDataSync(businesstype):
        """Synchronous version for used inside bulk loops"""
        return {
            NAMES.IMAGE_SQ_URL: businesstype.imageSQUrl,
            NAMES.IMAGE_RT_URL: businesstype.imageRTUrl,
            NAMES.ID: businesstype.id,
            NAMES.LABEL: businesstype.lable,
            NAMES.VALUE: businesstype.value,
        }

    @classmethod
    async def GetBusinessTypeData(cls, businesstype):
        return cls.GetBusinessTypeDataSync(businesstype)