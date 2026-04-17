from asgiref.sync import sync_to_async
from django.db import models, transaction
from django.db.models import Q
from django.core.paginator import Paginator
from django.utils import timezone
import asyncio
from typing import List, Dict, Any, Optional
from interior_admin.models import GMBBusiness
from interior_admin.Utils.RankingAlgo import RankingAlgo
from app_ib.Utils.Names import NAMES
from datetime import datetime

class GMBLeadsTasks:
    @staticmethod
    def SerializeGMBBusiness(business: GMBBusiness) -> Dict[str, Any]:
        """
        Sync serializer for GMBBusiness instances.
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
    async def GetGMBBusinessTask(business: GMBBusiness) -> Dict[str, Any]:
        """
        Legacy wrapper for SerializeGMBBusiness.
        """
        return GMBLeadsTasks.SerializeGMBBusiness(business)

    @staticmethod
    @sync_to_async
    @transaction.atomic
    def BulkIngestLeads(data_list: List[Dict[str, Any]]) -> int:
        """
        Performs bulk ingestion with manual change logging to ensure high performance
        while preserving custom model logic.
        """
        # 1. Identifier Mapping (Name + Phone)
        identifiers = []
        for item in data_list:
            name = item.get(NAMES.BUSINESS_NAME) or item.get(NAMES.BUSINESS_NAME_SNAKE)
            phone = item.get(NAMES.PHONE) or item.get(NAMES.PHONE_SNAKE, '')
            if name:
                identifiers.append((name, phone))
        
        if not identifiers:
            return 0

        # 2. Fetch existing records in one query
        query = Q()
        for name, phone in identifiers:
            query |= Q(businessName=name, phone=phone)
        
        existing_businesses = { (b.businessName, b.phone): b for b in GMBBusiness.objects.filter(query) }
        
        to_create = []
        to_update = []
        
        # 3. Process records
        for item in data_list:
            name = item.get(NAMES.BUSINESS_NAME) or item.get(NAMES.BUSINESS_NAME_SNAKE)
            phone = item.get(NAMES.PHONE) or item.get(NAMES.PHONE_SNAKE, '')
            if not name:
                continue
                
            ranking_info = RankingAlgo.calculate_score(item)
            wa_message = RankingAlgo.generate_wa_message(phone, name)
            
            payload = {
                "rating": item.get(NAMES.RATING, NAMES.DEFAULT_RATING),
                "ratingValue": ranking_info[NAMES.RATING_VALUE],
                "reviewCount": ranking_info[NAMES.REVIEW_COUNT],
                "address": item.get(NAMES.ADDRESS) or item.get(NAMES.ADDRESS_SNAKE, ''),
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

            business = existing_businesses.get((name, phone))
            
            if business:
                # Manual change tracking (replicating model.save logic for performance)
                events = []
                # Fields we track for logs as per GMBBusiness._get_log_state
                track_fields = {
                   "rankingRate": payload["rankingRate"],
                   "tier": payload["tier"],
                   "remark": payload["remark"]
                }
                
                # Check for changes
                if business.rankingRate != track_fields["rankingRate"]:
                    events.append(f"rankingRate updated from '{business.rankingRate}' to '{track_fields['rankingRate']}'")
                if business.tier != track_fields["tier"]:
                    events.append(f"tier updated from '{business.tier}' to '{track_fields['tier']}'")
                if business.remark != track_fields["remark"]:
                    events.append(f"remark updated from '{business.remark}' to '{track_fields['remark']}'")

                # Update the instance
                for field, value in payload.items():
                    setattr(business, field, value)
                
                if events:
                    if not isinstance(business.logs, list):
                        business.logs = []
                    business.logs.append({
                        NAMES.EVENT: ", ".join(events),
                        NAMES.TIMESTAMP: datetime.now().strftime(NAMES.DMY_12M),
                        NAMES.TRIGGERED_BY: NAMES.SYSTEM_USER
                    })
                
                to_update.append(business)
            else:
                # New record
                new_biz = GMBBusiness(
                    businessName=name,
                    phone=phone,
                    **payload
                )
                new_biz.logs = [{
                    NAMES.EVENT: NAMES.GMB_LEAD_CREATED,
                    NAMES.TIMESTAMP: datetime.now().strftime(NAMES.DMY_12M),
                    NAMES.TRIGGERED_BY: NAMES.SYSTEM_USER
                }]
                to_create.append(new_biz)

        # 4. Final DB Operations
        if to_create:
            GMBBusiness.objects.bulk_create(to_create)
        if to_update:
            GMBBusiness.objects.bulk_update(to_update, fields=[
                "rating", "ratingValue", "reviewCount", "address", "web", "mapLink", 
                "socialLinks", "waMessage", "rankingRate", "tier", "platform", 
                "category", "remark", "logs"
            ])
            
        return len(to_create) + len(to_update)

    @staticmethod
    async def IngestGMBDataTask(data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Optimized implementation using BulkIngestLeads.
        """
        if not isinstance(data_list, list):
            data_list = [data_list]
            
        processed_count = await GMBLeadsTasks.BulkIngestLeads(data_list)
        return {NAMES.PROCESSED_COUNT: processed_count, NAMES.TOTAL_RECEIVED: len(data_list)}

    @staticmethod
    async def PaginateGMBLeadsTask(filters_q: Q, sort_field: str, page_no: int, page_size: int) -> Dict[str, Any]:
        """
        Refactored pagination logic with CPU-efficient serialization.
        """
        def _get_page_data():
            leads_qs = GMBBusiness.objects.filter(filters_q).order_by(
                sort_field, f'-{NAMES.REVIEW_COUNT}', f'-{NAMES.RATING_VALUE}'
            ).select_related('assignedUser') # Optimize user lookup
            
            total_count = leads_qs.count()
            paginator = Paginator(leads_qs, page_size)
            page_obj = paginator.get_page(page_no)
            
            # Efficient sync mapping
            leads_details = [GMBLeadsTasks.SerializeGMBBusiness(lead) for lead in page_obj]
            
            return {
                NAMES.LEADS: leads_details,
                NAMES.CURRENT_PAGE: page_obj.number,
                NAMES.HAS_NEXT: page_obj.has_next(),
                NAMES.HAS_PREVIOUS: page_obj.has_previous(),
                NAMES.TOTAL_PAGES: paginator.num_pages,
                NAMES.TOTAL_COUNT: total_count,
            }

        result = await sync_to_async(_get_page_data)()
        result[NAMES.PAGE_SIZE] = page_size
        return result

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
