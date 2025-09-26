from asgiref.sync import sync_to_async
from app_ib.models import Business, LeadQuery, BusinessPlan
from django.utils import timezone
from datetime import timedelta
from django.utils.dateparse import parse_datetime
from django.core.paginator import Paginator
from app_ib.Utils.MyMethods import MY_METHODS


class ADMIN_PANEL_TASKS:
    
    @classmethod
    async def GetTotalActiveBusinesses(cls):
        try:
            active_businesses = await sync_to_async(
                lambda: BusinessPlan.objects.filter(expire_date__gte=timezone.now()).values_list('business_id', flat=True).distinct().count()
            )()
            return active_businesses
        except Exception as e:
            await MY_METHODS.printStatus(f"Error in GetTotalActiveBusinesses: {e}")
            return None
        
    @classmethod
    async def GetTotalInactiveBusinesses(cls):
        try:
            active_ids = await sync_to_async(
                lambda: list(BusinessPlan.objects.filter(expire_date__gte=timezone.now()).values_list('business_id', flat=True))
            )()
            inactive_count = await sync_to_async(
                lambda: Business.objects.exclude(id__in=active_ids).count()
            )()
            return inactive_count
        except Exception as e:
            await MY_METHODS.printStatus(f"Error in GetTotalInactiveBusinesses: {e}")
            return None
    @classmethod
    async def GetTotalBusinesses(cls):
        try:
            count = await sync_to_async(Business.objects.count)()
            return count
        except Exception as e:
            await MY_METHODS.printStatus(f"Error in GetTotalBusinesses: {e}")
            return None
    @classmethod
    async def GetWeeklySignups(cls):
        try:
            last_week = timezone.now() - timedelta(days=7)
            count = await sync_to_async(
                lambda: Business.objects.filter(timestamp__gte=last_week).count()
            )()
            return count
        except Exception as e:
            await MY_METHODS.printStatus(f"Error in GetWeeklySignups: {e}")
            return None

    @classmethod
    async def GetBusinessTiles(cls, start_date=None, end_date=None, page_number=1, page_size=2):
        try:
            businesses = Business.objects.all()

            # Apply date filters if provided
            if start_date:
                start_date = parse_datetime(start_date)
                businesses = businesses.filter(timestamp__gte=start_date)
            if end_date:
                end_date = parse_datetime(end_date)
                businesses = businesses.filter(timestamp__lte=end_date)

            # Pagination: Apply Django Paginator
            paginator = Paginator(businesses, page_size)  # Set the number of items per page
            page = paginator.page(page_number)  # Get the specific page

            business_list = await sync_to_async(list)(page.object_list)
            results = []

            for business in business_list:
                business_id = business.pk

                # Latest plan for the business
                plan = await sync_to_async(
                    lambda: BusinessPlan.objects.filter(business_id=business_id).order_by('-id').first()
                )()
                plan_name = plan.plan_name if plan else "No Plan"

                # Platform leads = no business assigned
                platform_leads_count = await sync_to_async(
                    lambda: LeadQuery.objects.filter(business=None).count()
                )()

                # Assigned leads = leads that are assigned to this business
                assigned_leads_count = await sync_to_async(
                    lambda: LeadQuery.objects.filter(business=business).count()
                )()

                total_leads = assigned_leads_count + platform_leads_count

                results.append({
                    "id": business_id,
                    "joinAt": business.timestamp,
                    "name": business.business_name,
                    "plan": plan_name,
                    "assignedLead": assigned_leads_count,
                    "platformLead": platform_leads_count,
                    "totalLeads": total_leads,
                    "date": timezone.now().date()
                })

            # Return paginated response
            return {
                "results": results,
                "totalPages": paginator.num_pages,
                "currentPage": page_number,
                "totalItems": paginator.count,
                'hasNext': page.has_next(),
                'hasPrevious': page.has_previous()
            }

        except Exception as e:
            await MY_METHODS.printStatus(f"Error in GetBusinessTiles: {e}")
            return None


