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
            NAMES.STATUS: business.status,
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
            NAMES.STATE: business.state,
            NAMES.CREATED_AT: business.createdAt.isoformat() if business.createdAt else None,
            NAMES.UPDATED_AT: business.updatedAt.isoformat() if business.updatedAt else None,
        }

    @staticmethod
    async def IngestSingleLeadTask(item: Dict[str, Any], trigger_user: Any = None) -> bool:
        """
        Processes a single lead. Wrapped for safety during bulk ingestion.
        """
        try:
            business_name = item.get(NAMES.BUSINESS_NAME) or item.get(NAMES.BUSINESS_NAME_SNAKE) or item.get('title') or item.get('name')
            if not business_name:
                return False
            
            ranking_info = RankingAlgo.calculate_score(item)
            wa_message = RankingAlgo.generate_wa_message(item.get(NAMES.PHONE) or item.get(NAMES.PHONE_SNAKE, ''), business_name)
            
            lead, _ = await sync_to_async(GMBBusiness.objects.update_or_create)(
                businessName=business_name,
                phone=item.get(NAMES.PHONE) or item.get(NAMES.PHONE_SNAKE, ''),
                defaults={
                    NAMES.RATING.lower(): item.get(NAMES.RATING) or NAMES.DEFAULT_RATING,
                    NAMES.RATING_VALUE: ranking_info[NAMES.RATING_VALUE],
                    NAMES.REVIEW_COUNT: ranking_info[NAMES.REVIEW_COUNT],
                    NAMES.ADDRESS.lower(): item.get(NAMES.ADDRESS) or item.get(NAMES.ADDRESS_SNAKE, ''),
                    "web": item.get(NAMES.WEBSITE) or item.get(NAMES.WEBSITE_URL) or item.get(NAMES.WEBSITE_LINK),
                    "mapLink": item.get(NAMES.MAP_LINK_SNAKE) or item.get(NAMES.MAPS_LINK_SNAKE) or item.get(NAMES.GMB_LINK),
                    "socialLinks": item.get(NAMES.SOCIAL_LINKS) or item.get(NAMES.SOCIAL_LINKS_SNAKE) or [],
                    "waMessage": wa_message,
                    "rankingRate": ranking_info[NAMES.RANKING_RATE],
                    "tier": ranking_info[NAMES.TIER],
                    "platform": item.get(NAMES.PLATFORM, NAMES.DEFAULT_PLATFORM),
                    "category": item.get(NAMES.CATEGORY),
                    "state": item.get(NAMES.STATE) or item.get("state_name") or item.get("region"),
                    "remark": item.get(NAMES.REMARK)
                }
            )
            
            return True
        except Exception as e:
            msg = f"Error ingesting lead {item.get(NAMES.BUSINESS_NAME, NAMES.UNKNOWN_BUSINESS)}: {e}"
            print(msg)
            try:
                with open("/Users/nikhil/Desktop/Offfice/interior_bazar/ingest_errors.log", "a") as f:
                    f.write(msg + "\n")
            except:
                pass
            return False

    @staticmethod
    async def IngestGMBDataTask(data_list: List[Dict[str, Any]], trigger_user: Any = None, assignable_users: List[Any] = None) -> Dict[str, Any]:
        """
        Bulk ingests GMB data. Continues processing even if individual records fail.
        If assignable_users are provided, it performs a balanced distribution.
        """
        if not isinstance(data_list, list):
            data_list = [data_list]
            
        results = []
        for item in data_list:
            res = await GMBLeadsTasks.IngestSingleLeadTask(item, trigger_user=trigger_user)
            results.append(res)
        
        # If sales team exists, trigger auto-assignment for unassigned leads
        if assignable_users:
            await GMBLeadsTasks.AutoAssignUnassignedLeadsTask(assignable_users, trigger_user)
        
        processed_count = sum(1 for r in results if r)
        return {NAMES.PROCESSED_COUNT: processed_count, NAMES.TOTAL_RECEIVED: len(data_list)}

    @staticmethod
    async def AutoAssignUnassignedLeadsTask(assignable_users: List[Any], trigger_user: Any = None) -> Dict[str, Any]:
        """
        Scans for all unassigned leads and distributes them across assignable_users.
        """
        if not assignable_users:
            return {NAMES.PROCESSED_COUNT: 0, "message": "No assignable users found"}
            
        # Fetch all unassigned leads
        unassigned_leads = await sync_to_async(lambda: list(GMBBusiness.objects.filter(assignedUser__isnull=True).order_by('createdAt')))()
        
        if not unassigned_leads:
            return {NAMES.PROCESSED_COUNT: 0}

        # Balanced distribution (round-robin)
        for i, lead in enumerate(unassigned_leads):
            target_user = assignable_users[i % len(assignable_users)]
            lead.assignedUser = target_user
            lead.status = NAMES.NEW
            lead._triggered_by = trigger_user
            await sync_to_async(lead.save)()
            
        return {NAMES.PROCESSED_COUNT: len(unassigned_leads)}

    @staticmethod
    async def PaginateGMBLeadsTask(filters_q: Q, sort_field: str, page_no: int, page_size: int) -> Dict[str, Any]:
        """
        Handles pagination logic for GMB leads.
        """
        print(f"[DEBUG] PaginateGMBLeadsTask: Querying GMBBusiness with filters: {filters_q}")
        print(f"[DEBUG] PaginateGMBLeadsTask: Sort field: {sort_field}")
        
        leads_qs = await sync_to_async(
            lambda: GMBBusiness.objects.filter(filters_q).order_by(sort_field, f'-{NAMES.REVIEW_COUNT}', f'-{NAMES.RATING_VALUE}')
        )()
        
        total_count = await sync_to_async(leads_qs.count)()
        print(f"[DEBUG] PaginateGMBLeadsTask: Total leads matching filters: {total_count}")
        
        paginator = Paginator(leads_qs, page_size)
        page_obj = paginator.get_page(page_no)
        print(f"[DEBUG] PaginateGMBLeadsTask: Fetched page {page_obj.number} of {paginator.num_pages}")

        tasks = [GMBLeadsTasks.GetGMBBusinessTask(lead) for lead in page_obj]
        leads_details = await asyncio.gather(*tasks)
        print(f"[DEBUG] PaginateGMBLeadsTask: Serialized {len(leads_details)} leads for the current page")

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

    @staticmethod
    async def UpdateGMBLeadTask(lead_ins: GMBBusiness, data: Any, trigger_user: Any) -> Dict[str, Any]:
        """
        Updates specific fields of a GMB lead.
        """
        update_data = data.dict(exclude_none=True)
        
        # UI sends 'location', but model uses 'address'
        if 'location' in update_data:
            update_data['address'] = update_data.pop('location')
            
        for field, value in update_data.items():
            if hasattr(lead_ins, field):
                setattr(lead_ins, field, value)
        
        # Regenerate WhatsApp message if phone changes
        if 'phone' in update_data:
            lead_ins.waMessage = RankingAlgo.generate_wa_message(lead_ins.phone, lead_ins.businessName)

        # Recalculate ranking if relevant fields changed
        ranking_trigger_fields = {'address', 'phone', 'category', 'web'}
        if any(f in update_data for f in ranking_trigger_fields):
            ranking_payload = {
                NAMES.BUSINESS_NAME: lead_ins.businessName,
                NAMES.PHONE: lead_ins.phone,
                NAMES.ADDRESS: lead_ins.address,
                "web": lead_ins.web,
                NAMES.CATEGORY: lead_ins.category,
                NAMES.RATING.lower(): lead_ins.rating,
                "socialLinks": lead_ins.socialLinks
            }
            ranking_info = RankingAlgo.calculate_score(ranking_payload)
            lead_ins.rankingRate = ranking_info[NAMES.RANKING_RATE]
            lead_ins.tier = ranking_info[NAMES.TIER]

        # Set trigger user for logging
        lead_ins._triggered_by = trigger_user
        await sync_to_async(lead_ins.save)()
        
        return await GMBLeadsTasks.GetGMBBusinessTask(lead_ins)


    @staticmethod
    async def CreateSingleLeadTask(item: Dict[str, Any], trigger_user: Any) -> Dict[str, Any]:
        """
        Creates a single lead and assigns it to the trigger_user.
        """
        success = await GMBLeadsTasks.IngestSingleLeadTask(item, trigger_user=trigger_user)
        if success:
            business_name = item.get(NAMES.BUSINESS_NAME) or item.get(NAMES.BUSINESS_NAME_SNAKE)
            phone = item.get(NAMES.PHONE) or item.get(NAMES.PHONE_SNAKE, '')
            
            lead = await sync_to_async(GMBBusiness.objects.get)(businessName=business_name, phone=phone)
            
            if trigger_user and trigger_user.is_authenticated:
                lead.assignedUser = trigger_user
                lead.status = NAMES.STATUS_ASSIGNED
                lead._triggered_by = trigger_user
                await sync_to_async(lead.save)()
            
            return await GMBLeadsTasks.GetGMBBusinessTask(lead)
        return None

    @staticmethod
    async def GetLeadsKPIsTask() -> Dict[str, Any]:
        """
        Returns unique values and counts for dashboard filters.
        Normalized to ensure unique labels despite casing.
        """
        def get_aggregates():
            from django.db.models import Count
            
            # Fields mapping: Frontend Key -> DB Field
            mapping = {
                "state": "state",
                "city": "address",
                "status": "status",
                "platform": "platform",
                "rating": "rating"
            }
            
            raw_aggregates = {}
            for fe_key, db_field in mapping.items():
                raw_aggregates[fe_key] = list(
                    GMBBusiness.objects.values(db_field)
                    .annotate(count=Count('id'))
                    .order_by(db_field)
                )
            return raw_aggregates, mapping

        aggregates, field_mapping = await sync_to_async(get_aggregates)()
        
        formatted_data = {}
        for fe_key, rows in aggregates.items():
            db_field = field_mapping[fe_key]
            normalized = {}
            
            for row in rows:
                val = str(row[db_field] or "").strip()
                if not val:
                    continue
                
                # Normalize key to upper case to merge "Mumbai" and "mumbai"
                norm_key = val.upper()
                
                if norm_key in normalized:
                    normalized[norm_key]["count"] += row["count"]
                else:
                    normalized[norm_key] = {
                        "label": val,  # Keep the casing of the first encountered version
                        "value": val,
                        "count": row["count"]
                    }
            
            # Sort normalized values by label alphabet
            formatted_data[fe_key] = sorted(normalized.values(), key=lambda x: x["label"])

        return formatted_data

GMB_LEADS_TASKS = GMBLeadsTasks()
