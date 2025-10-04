from app_ib.models import Business,Location,BusinessBadge,BusinessType,BusinessCategory,BusinessSegment
import asyncio
from asgiref.sync import sync_to_async
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.Controllers.BussLocation.Tasks.BusinessLocationTasks import BUSS_LOC_TASK
from app_ib.Utils.MyMethods import MY_METHODS
from django.db.models import Prefetch
class BUSS_TASK:
    @classmethod
    async def CreateBusinessTask(cls, user_ins, data):
        try:
            badge = await sync_to_async(lambda: BusinessBadge.objects.filter(isDefault=True).first())()

            # Get business type (FK)
            business_type_id = getattr(data.businessType, 'id', None)
            business_type = await sync_to_async(lambda: BusinessType.objects.filter(id=business_type_id).first())()

            # Validate and fetch segments (max 5)
            segment_ids = [seg.id for seg in getattr(data, 'segments', [])]
            if len(segment_ids) > 5:
                return None  # Too many segments
            segments = await sync_to_async(lambda: list(BusinessSegment.objects.filter(id__in=segment_ids)))()
            if len(segments) != len(segment_ids):
                return None  # Invalid segment IDs

            # Validate and fetch categories (max 3)
            category_ids = [cat.id for cat in getattr(data, 'categories', [])]
            if len(category_ids) > 3:
                return None  # Too many categories
            categories = await sync_to_async(lambda: list(BusinessCategory.objects.filter(id__in=category_ids)))()
            if len(categories) != len(category_ids):
                return None  # Invalid category IDs

            # Create Business instance
            business_ins = Business()
            business_ins.user = user_ins
            business_ins.business_name = getattr(data, 'businessName', "")
            business_ins.whatsapp = getattr(data, 'whatsapp', "")
            business_ins.gst = getattr(data, 'gst', "")
            business_ins.since = getattr(data, 'since', "")
            business_ins.bio = getattr(data, 'bio', "")
            business_ins.cover_image_url = getattr(data, 'coverImageUrl', "")
            business_ins.business_type = business_type
            business_ins.businessBadge = badge

            # Optional legacy text (store labels)
            business_ins.segment = ", ".join([s.lable for s in segments])
            business_ins.catigory = ", ".join([c.lable for c in categories])

            await sync_to_async(business_ins.save)()

            # Set M2M relations
            await sync_to_async(business_ins.businessSegment.set)(segments)
            await sync_to_async(business_ins.businessCategory.set)(categories)

            return True

        except Exception as e:
            return None
    @classmethod
    async def UpdateBusinessTask(cls, business_ins, data):
        try:
            # Related instances (nullable)
            loc = getattr(business_ins, 'business_location', None)
            prof = getattr(business_ins, 'business_profile', None)

            # --- ForeignKey: BusinessType ---
            if hasattr(data, 'businessType') and getattr(data.businessType, 'id', None):
                business_type = await sync_to_async(BusinessType.objects.filter(id=data.businessType.id).first)()
                if business_type:
                    business_ins.business_type = business_type

            # --- M2M: BusinessSegment (max 5) ---
            segments = getattr(data, 'segments', None)
            if isinstance(segments, list) and len(segments) <= 5:
                segment_ids = [s.id for s in segments]
                segment_objs = await sync_to_async(lambda: list(BusinessSegment.objects.filter(id__in=segment_ids)))()
                if len(segment_objs) == len(segment_ids):
                    await sync_to_async(business_ins.businessSegment.set)(segment_objs)
                    business_ins.segment = ", ".join([s.lable for s in segment_objs])  # legacy

            # --- M2M: BusinessCategory (max 3) ---
            categories = getattr(data, 'categories', None)
            if isinstance(categories, list) and len(categories) <= 3:
                category_ids = [c.id for c in categories]
                category_objs = await sync_to_async(lambda: list(BusinessCategory.objects.filter(id__in=category_ids)))()
                if len(category_objs) == len(category_ids):
                    await sync_to_async(business_ins.businessCategory.set)(category_objs)
                    business_ins.catigory = ", ".join([c.lable for c in category_objs])  # legacy

            # --- Simple Fields ---
            business_ins.business_name = getattr(data, 'businessName', business_ins.business_name)
            business_ins.gst = getattr(data, 'gst', business_ins.gst)
            business_ins.since = getattr(data, 'since', business_ins.since)
            business_ins.bio = getattr(data, 'bio', business_ins.bio)
            business_ins.cover_image_url = getattr(data, 'coverImageUrl', business_ins.cover_image_url)
            await sync_to_async(business_ins.save)()

            # --- Business Location (if exists) ---
            if loc:
                await BUSS_LOC_TASK.UpdateBusinessLocTask(loc, data)
            else:
                await BUSS_LOC_TASK.CreateBusinessLocTask(business_ins, data)

            # --- Business Profile (if exists) ---
            if prof and hasattr(data, 'youtubeLink'):
                prof.youtube_link = getattr(data, 'youtubeLink')
                await sync_to_async(prof.save)()

            return await cls.GetBusinessInfo(business_ins.id)

        except Exception as e:
            #await MY_METHODS.printStatus(f'Error in UpdateBusinessTask: {e}')
            return None

    @classmethod
    async def GetBusinessInfo(cls, id):
        try:
            business_ins = await sync_to_async(Business.objects.get)(pk=id)
            business_loc_ins = getattr(business_ins, 'business_location', None)
            business_prof_ins = getattr(business_ins, 'business_profile', None)

            # Get related segments and categories (as objects)
            segments = await sync_to_async(lambda: list(business_ins.businessSegment.all()))()
            categories = await sync_to_async(lambda: list(business_ins.businessCategory.all()))()

            # Serialize them
            segment_data = [await cls.GetBusinessTypeData(seg) for seg in segments]
            category_data = [await cls.GetBusinessTypeData(cat) for cat in categories]

            data = {
                'businessName': business_ins.business_name,
                'segments': segment_data,
                'categories': category_data,
                'whatsapp': business_ins.whatsapp,
                'gst': business_ins.gst,
                'coverImageUrl': business_ins.cover_image_url,
                'since': business_ins.since,
                'id': business_ins.id,
                'bio': business_ins.bio,
                'updatedAt': business_ins.updated_at,
                'badge': business_ins.businessBadge.image_url if business_ins.businessBadge else None,
            }

            # Serialize business type
            if business_ins.business_type:
                data['businessType'] = await cls.GetBusinessTypeData(business_ins.business_type)

            # Location
            if business_loc_ins:
                location = await BUSS_LOC_TASK.GetBusinessLocTask(business_loc_ins)
                data['location_link'] = location["location_link"]
                data['pin_code'] =location['pin_code']
                data['city'] = location['city']
                data['state'] = location['state']
                data['country'] = location['country']

            # Profile
            if business_prof_ins:
                data['youtube_link'] = business_prof_ins.youtube_link

            return data

        except Exception as e:
            #await MY_METHODS.printStatus(f'Error in GetBusinessInfo: {e}')
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
            business_profile = getattr(business_ins, 'business_profile', None)
            business_image = business_profile.primary_image_url if business_profile else None

            # Segments
            segments = await sync_to_async(lambda: list(business_ins.businessSegment.all()))()
            segment_data = [await cls.GetBusinessTypeData(seg) for seg in segments]

            # Categories
            categories = await sync_to_async(lambda: list(business_ins.businessCategory.all()))()
            category_data = [await cls.GetBusinessTypeData(cat) for cat in categories]

            # Business Type
            business_type_data = None
            if business_ins.business_type:
                business_type_data = await cls.GetBusinessTypeData(business_ins.business_type)

            # Final response
            data = {
                'id': business_ins.id,
                'businessName': business_ins.business_name,
                'coverImageUrl': business_ins.cover_image_url,
                'since': business_ins.since,
                'businessImage': business_image,
                'segments': segment_data,
                'categories': category_data,
                'businessType': business_type_data,
            }

            return data

        except Exception as e:
            #await MY_METHODS.printStatus(f'Error in GetBusinessInfoForSearch: {e}')
            return None

    @classmethod
    async def GetBusinessTypeData(cls,businesstype):
        try:
            typeData={
                'id': businesstype.id,
                'label': businesstype.lable,
                'value': businesstype.value,
            }

            return typeData
        except Exception as e:
            #await MY_METHODS.printStatus(f'Error in GetAllBusinessTypes: {e}')
            return None