from asgiref.sync import sync_to_async
from django.db.models import Q
from django.core.paginator import Paginator
import asyncio
from interior_admin.models import GMBBusiness, GMBActivityLog
from interior_admin.Utils.RankingAlgo import RankingAlgo

from asgiref.sync import sync_to_async
from django.db.models import Q
from django.core.paginator import Paginator
import asyncio
from typing import List, Dict, Any, Optional
from interior_admin.models import GMBBusiness
from interior_admin.Utils.RankingAlgo import RankingAlgo
from app_ib.Utils.Names import NAMES

class GMBLeadsTasks:
    @staticmethod
    async def GetGMBBusinessTask(business: GMBBusiness) -> Dict[str, Any]:
        """
        Serializes a GMBBusiness instance into a dictionary.
        """
        return {
            NAMES.ID: business.id,
            NAMES.BUSINESS_NAME: business.businessName,
            NAMES.RATING: business.rating,
            NAMES.RATING_VALUE: business.ratingValue,
            NAMES.REVIEW_COUNT: business.reviewCount,
            NAMES.ADDRESS: business.address,
            NAMES.PHONE: business.phone,
            NAMES.WEBSITE: business.web,
            NAMES.GMB_LINK: business.mapLink,
            NAMES.SOCIAL_LINKS: business.socialLinks,
            NAMES.WA_MESSAGE: business.waMessage,
            NAMES.ASSIGNED_USER: business.assignedUser.username if business.assignedUser else None,
            NAMES.ASSIGNED_USER_ID: business.assignedUser.id if business.assignedUser else None,
            NAMES.RANKING_RATE: business.rankingRate,
            NAMES.TIER: business.tier,
            NAMES.PLATFORM: business.platform,
            NAMES.REMARK: business.remark,
            NAMES.CATEGORY: business.category,
            NAMES.LOGS: business.logs,
            NAMES.CREATED_AT: business.createdAt.isoformat() if business.createdAt else None,
            NAMES.UPDATED_AT: business.updatedAt.isoformat() if business.updatedAt else None,
        }

    @staticmethod
    async def IngestSingleLeadTask(item: Dict[str, Any]) -> bool:
        """
        Processes a single lead. Wrapped for safety during bulk ingestion.
        """
        try:
            business_name = item.get(NAMES.BUSINESS_NAME) or item.get(NAMES.BUSINESS_NAME_SNAKE)
            if not business_name:
                return False
            
            ranking_info = RankingAlgo.calculate_score(item)
            wa_message = RankingAlgo.generate_wa_message(item.get(NAMES.PHONE) or item.get(NAMES.PHONE_SNAKE, ''), business_name)
            
            await sync_to_async(GMBBusiness.objects.update_or_create)(
                businessName=business_name,
                phone=item.get(NAMES.PHONE) or item.get(NAMES.PHONE_SNAKE, ''),
                defaults={
                    NAMES.RATING.lower(): item.get(NAMES.RATING, NAMES.DEFAULT_RATING),
                    NAMES.RATING_VALUE: ranking_info[NAMES.RATING_VALUE],
                    NAMES.REVIEW_COUNT: ranking_info[NAMES.REVIEW_COUNT],
                    NAMES.ADDRESS.lower(): item.get(NAMES.ADDRESS) or item.get(NAMES.ADDRESS_SNAKE, ''),
                    "web": item.get(NAMES.WEBSITE) or item.get(NAMES.WEBSITE_URL) or item.get(NAMES.WEBSITE_LINK),
                    "mapLink": item.get(NAMES.MAP_LINK_SNAKE) or item.get(NAMES.MAPS_LINK_SNAKE) or item.get(NAMES.GMB_LINK),
                    "socialLinks": item.get(NAMES.SOCIAL_LINKS, []) or item.get(NAMES.SOCIAL_LINKS_SNAKE, []),
                    "waMessage": wa_message,
                    "rankingRate": ranking_info[NAMES.RANKING_RATE],
                    "tier": ranking_info[NAMES.TIER],
                    "platform": item.get(NAMES.PLATFORM, NAMES.DEFAULT_PLATFORM),
                    "category": item.get(NAMES.CATEGORY),
                    "remark": item.get(NAMES.REMARK)
                }
            )
            return True
        except Exception as e:
            print(f"Error ingesting lead {item.get(NAMES.BUSINESS_NAME, NAMES.UNKNOWN_BUSINESS)}: {e}")
            return False

    @staticmethod
    async def IngestGMBDataTask(data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Bulk ingests GMB data. Continues processing even if individual records fail.
        """
        if not isinstance(data_list, list):
            data_list = [data_list]
            
        tasks = [GMBLeadsTasks.IngestSingleLeadTask(item) for item in data_list]
        results = await asyncio.gather(*tasks)
        
        processed_count = sum(1 for r in results if r)
        return {NAMES.PROCESSED_COUNT: processed_count, NAMES.TOTAL_RECEIVED: len(data_list)}

    @staticmethod
    async def PaginateGMBLeadsTask(filters_q: Q, sort_field: str, page_no: int, page_size: int) -> Dict[str, Any]:
        """
        Handles pagination logic for GMB leads.
        """
        leads_qs = await sync_to_async(
            lambda: GMBBusiness.objects.filter(filters_q).order_by(sort_field, f'-{NAMES.REVIEW_COUNT}', f'-{NAMES.RATING_VALUE}')
        )()
        
        total_count = await sync_to_async(leads_qs.count)()
        paginator = Paginator(leads_qs, page_size)
        page_obj = paginator.get_page(page_no)

        tasks = [GMBLeadsTasks.GetGMBBusinessTask(lead) for lead in page_obj]
        leads_details = await asyncio.gather(*tasks)

        return {
            NAMES.LEADS: leads_details,
            NAMES.CURRENT_PAGE: page_obj.number,
            NAMES.HAS_NEXT: page_obj.has_next(),
            NAMES.HAS_PREVIOUS: page_obj.has_previous(),
            NAMES.TOTAL_PAGES: paginator.num_pages,
            NAMES.TOTAL_COUNT: total_count,
            NAMES.PAGE_SIZE: page_size
        }

    @staticmethod
    async def AssignLeadTask(lead_ins: GMBBusiness, target_user_ins: Any, trigger_user_ins: Any) -> Dict[str, Any]:
        """
        Assigns a lead to a user.
        """
        lead_ins.assignedUser = target_user_ins
        lead_ins._triggered_by = trigger_user_ins
        await sync_to_async(lead_ins.save)()
        return {NAMES.STATUS_KEY: NAMES.STATUS_ASSIGNED, NAMES.USER: target_user_ins.username}

GMB_LEADS_TASKS = GMBLeadsTasks()

GMB_LEADS_TASKS = GMBLeadsTasks()
