from app_ib.models import (
    Business, Location, BusinessBadge, BusinessType, BusinessCategory,
    BusinessSegment, BusinessSocialMedia, UserProfile, BusinessProfile, CustomUser
)
import asyncio
import random
from asgiref.sync import sync_to_async
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.Utils.Names import NAMES
from interior_business.Controllers.BussLocation.Tasks.BusinessLocationTasks import BUSS_LOC_TASK
from app_ib.Utils.MyMethods import MY_METHODS
from django.db.models import Prefetch

class BUSS_TASK:

    @classmethod
    async def CreateCategoryTask(cls, data):
        try:
            lable = await sync_to_async(lambda: MY_METHODS.slugify(data.label))()
            count = await sync_to_async(BusinessCategory.objects.count)()
            newCategory = await sync_to_async(BusinessCategory.objects.create)(
                lable=lable, value=data.label, index=count + 1
            )
            return newCategory.id
        except: return None
    
    @classmethod
    async def CreateSegmentTask(cls, data):
        try:
            lable = await sync_to_async(lambda: MY_METHODS.slugify(data.label))()
            newSegment = await sync_to_async(BusinessSegment.objects.create)(
                lable=lable, value=data.label
            )
            return newSegment.id
        except: return None

    @classmethod
    async def GetBusinessHeaderTask(cls, business_ins: Business):
        """Optimized header fetch"""
        try:
            queryset = Business.objects.filter(pk=business_ins.pk).select_related(
                'user', 'user__user_profile', 'business_profile'
            ).prefetch_related(
                Prefetch('businessSocialMedia', queryset=BusinessSocialMedia.objects.select_related('socialMedia'))
            )
            business = await sync_to_async(queryset.first)()
            if not business: return "Business not found", False

            social_links = {
                NAMES.LINKEDIN_LINK: NAMES.EMPTY,
                NAMES.WHATSAPP_LINK: business.whatsapp or NAMES.EMPTY,
                NAMES.FACEBOOK_LINK: NAMES.EMPTY,
                NAMES.INSTAGRAM_LINK: NAMES.EMPTY,
            }

            for sm in business.businessSocialMedia.all():
                name = sm.socialMedia.name.lower()
                if name == NAMES.LINKEDIN: social_links[NAMES.LINKEDIN_LINK] = sm.link
                elif name == NAMES.FACEBOOK: social_links[NAMES.FACEBOOK_LINK] = sm.link
                elif name == NAMES.INSTAGRAM: social_links[NAMES.INSTAGRAM_LINK] = sm.link

            profile_image = business.business_profile.primaryImageUrl if business.business_profile else NAMES.EMPTY
            user_profile = getattr(business.user, 'user_profile', None)
            
            data = {
                NAMES.BUSINESS_NAME: business.businessName or NAMES.EMPTY,
                NAMES.DESCRIPTION: business.bio or NAMES.EMPTY,
                NAMES.SOCIAL_MEDIA: social_links,
                NAMES.PROFILE_IMAGE_URL: profile_image,
                NAMES.BANNER_IMAGE_URL: business.bannerImageUrl or NAMES.EMPTY,
                NAMES.PHONE: user_profile.phone if user_profile else NAMES.EMPTY,
                NAMES.COUNTRY_CODE: user_profile.countryCode if user_profile else NAMES.EMPTY,
            }
            return data, True
        except Exception as e:
            return str(e), False

    @classmethod
    async def GetBusinessContactInfoTask(cls, business_ins: Business):
        """Optimized contact info fetch"""
        try:
            queryset = Business.objects.filter(id=business_ins.id).select_related(
                'user__user_profile', 'business_location', 'business_location__locationState', 'business_location__locationCountry'
            )
            business = await sync_to_async(queryset.first)()
            if not business: return {NAMES.ERROR: 'Business not found'}

            website_link = await sync_to_async(
                lambda: BusinessSocialMedia.objects.filter(
                    business=business, socialMedia__name__iexact=NAMES.WEBSITE
                ).values_list('link', flat=True).first()
            )()

            loc = getattr(business, 'business_location', None)
            location = NAMES.EMPTY
            if loc:
                parts = [loc.city, loc.locationState.name if loc.locationState else None, loc.locationCountry.name if loc.locationCountry else None]
                location = ', '.join([p for p in parts if p])

            user_profile = getattr(business.user, 'user_profile', None)
            data = {
                NAMES.PHONE: user_profile.phone if user_profile else NAMES.EMPTY,
                NAMES.COUNTRY_CODE: user_profile.countryCode if user_profile else NAMES.EMPTY,
                NAMES.LOCATION: location,
                NAMES.EMAIL: user_profile.email if user_profile else NAMES.EMPTY,
                NAMES.GMB_LINK: loc.locationLink if loc else NAMES.EMPTY,
                NAMES.WEBSITE_LINK: website_link or NAMES.EMPTY
            }
            return data
        except: return None

    @classmethod
    async def BulkSerializeBusinessInfo(cls, business_list):
        """High-performance bulk serialization for interior_business"""
        results = []
        for business in business_list:
            try:
                loc_ins = getattr(business, 'business_location', None)
                prof_ins = getattr(business, 'business_profile', None)
                
                segment_data = [cls.GetBusinessTypeDataSync(seg) for seg in business.businessSegment.all()]
                category_data = [cls.GetBusinessTypeDataSync(cat) for cat in business.businessCategory.all()]

                data = {
                    NAMES.BUSINESS_NAME: business.businessName,
                    NAMES.BRAND_NAME: business.brandName,
                    NAMES.SEGMENTS: segment_data,
                    NAMES.CATEGORIES: category_data,
                    NAMES.WHATSAPP: business.whatsapp,
                    NAMES.GST: business.gst,
                    NAMES.COVER_IMAGE_URL: business.coverImageUrl or NAMES.EMPTY,
                    NAMES.BANNER_IMAGE_URL: business.bannerImageUrl or NAMES.EMPTY,
                    NAMES.SINCE: business.since,
                    NAMES.ID: business.id,
                    NAMES.BIO: business.bio,
                    NAMES.UPDATED_AT: business.updatedAt,
                    NAMES.BADGE: business.businessBadge.imageUrl if business.businessBadge else None,
                    NAMES.TIMESTAMP: business.timestamp
                }

                # Mock rating as per legacy logic
                rating = "4.2" # consistent mock
                data[NAMES.RATING] = rating
                data[NAMES.RATING_VALUE] = 4.2

                if business.businessType:
                    data[NAMES.BUSINESS_TYPE] = cls.GetBusinessTypeDataSync(business.businessType)

                if loc_ins:
                    data[NAMES.GMB_LINK] = loc_ins.locationLink
                    data[NAMES.PINCODE] = loc_ins.pinCode
                    data[NAMES.CITY] = loc_ins.city
                    data[NAMES.STATE] = {NAMES.ID: loc_ins.locationState.id, NAMES.NAME: loc_ins.locationState.name} if loc_ins.locationState else None
                    data[NAMES.COUNTRY] = {NAMES.ID: loc_ins.locationCountry.id, NAMES.NAME: loc_ins.locationCountry.code} if loc_ins.locationCountry else None

                if prof_ins:
                    data[NAMES.YOUTUBE_LINK] = prof_ins.youtubeLink

                results.append(data)
            except: pass
        return results

    @classmethod
    async def GetBusinessInfo(cls, id):
        try:
            queryset = Business.objects.filter(pk=id).select_related(
                'business_location', 'business_location__locationState', 
                'business_location__locationCountry', 'business_profile',
                'businessBadge', 'businessType'
            ).prefetch_related('businessSegment', 'businessCategory')
            
            business_list = await sync_to_async(list)(queryset)
            data_list = await cls.BulkSerializeBusinessInfo(business_list)
            return data_list[0] if data_list else None
        except: return None

    @classmethod
    async def GetBusinessInfoForSearch(cls, id):
        try:
            queryset = Business.objects.filter(pk=id).select_related('business_profile', 'businessType').prefetch_related('businessSegment', 'businessCategory')
            business = await sync_to_async(queryset.first)()
            if not business: return None

            segment_data = [cls.GetBusinessTypeDataSync(seg) for seg in business.businessSegment.all()]
            category_data = [cls.GetBusinessTypeDataSync(cat) for cat in business.businessCategory.all()]

            return {
                NAMES.ID: business.id,
                NAMES.BUSINESS_NAME: business.businessName,
                NAMES.BRAND_NAME: business.brandName,
                NAMES.COVER_IMAGE_URL: business.coverImageUrl,
                NAMES.SINCE: business.since,
                NAMES.BUSINESS_IMAGE: business.business_profile.primaryImageUrl if business.business_profile else None,
                NAMES.SEGMENTS: segment_data,
                NAMES.CATEGORIES: category_data,
                NAMES.BUSINESS_TYPE: cls.GetBusinessTypeDataSync(business.businessType) if business.businessType else None,
            }
        except: return None

    @staticmethod
    def GetBusinessTypeDataSync(businesstype):
        # Optimized without random number await loops
        return {
            NAMES.ID: businesstype.id,
            NAMES.LABEL: businesstype.lable,
            NAMES.VALUE: businesstype.value,
            NAMES.IMAGE_SQ_URL: businesstype.imageSQUrl or NAMES.RANDOM_SQ_IMAGE.replace('{num}', '1'),
            NAMES.IMAGE_RT_URL: businesstype.imageRTUrl or NAMES.RANDOM_RT_IMAGE.replace('{num}', '1'),
            NAMES.TRENDING: getattr(businesstype, 'trending', False),
            NAMES.SHORT_VALUE: getattr(businesstype, 'shortValue', '')
        }

    @classmethod
    async def GetBusinessTypeData(cls, businesstype):
        return cls.GetBusinessTypeDataSync(businesstype)

    @classmethod
    async def GetBusinessSegmentData(cls, segment):
        # Optimized to avoid hidden N+1 first() call
        return cls.GetBusinessTypeDataSync(segment)