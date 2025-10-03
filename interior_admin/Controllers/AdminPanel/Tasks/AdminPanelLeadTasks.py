from app_ib.models import LeadQuery,PlanQuery
from asgiref.sync import sync_to_async
from django.utils import timezone
from datetime import timedelta
from django.utils.dateparse import parse_datetime
from django.core.paginator import Paginator
from app_ib.Utils.MyMethods import MY_METHODS
from django.db.models import Q
class LEAD_TASKS:
    
    @classmethod
    async def GetTotalAssignedLeads(cls):
        try:
            assingedLeads = await sync_to_async(
                lambda: LeadQuery.objects.filter(business__isnull=False).count()
            )()
            return assingedLeads
        except Exception as e:
            #await MY_METHODS.printStatus(f"Error in GetTotalPlatformLeads: {e}")
            return None
    
    @classmethod
    async def GetPlatformLeads(cls):  
        try:
            assignedLeadsCount = await sync_to_async(
                lambda: PlanQuery.objects.filter().count()
            )()
            return assignedLeadsCount
        except Exception as e:
            #await MY_METHODS.printStatus(f"Error in GetTotalAssignedLeads: {e}")
            return None
    @classmethod
    async def GetTotalUnassignedLeads(cls):  
        try:
            unassignedCount = await sync_to_async(
                lambda: LeadQuery.objects.filter(business__isnull=True).count()
            )()
            return unassignedCount
        except Exception as e:
            #await MY_METHODS.printStatus(f"Error in GetTotalAssignedLeads: {e}")
            return None
    
    @classmethod
    async def GetTotalLeads(cls):
        try:
            unassignedLeads = await cls.GetTotalUnassignedLeads()
            assignedLeads = await cls.GetTotalAssignedLeads()
            platformLeads = await cls.GetPlatformLeads()
            return unassignedLeads + assignedLeads + platformLeads
        except Exception as e:
            #await MY_METHODS.printStatus(f"Error in GetTotalLeads: {e}")
            return None
    
    @classmethod
    async def GetTodayLeads(cls):
        try:
            today = timezone.now().date()
            todayLeads = await sync_to_async(
                lambda: LeadQuery.objects.filter(timestamp__date=today).count()
            )()
            return todayLeads
        except Exception as e:
            #await MY_METHODS.printStatus(f"Error in GetTodayLeads: {e}")
            return None


    @classmethod
    async def GetLeadTiles(cls, start_date=None, end_date=None, search_query=None, page_number=1, page_size=10):
        try:
            leads = LeadQuery.objects.all()

            # Apply date filters if provided
            if start_date:
                start_date = parse_datetime(start_date)
                leads = leads.filter(timestamp__gte=start_date)
            if end_date:
                end_date = parse_datetime(end_date)
                leads = leads.filter(timestamp__lte=end_date)

            # Apply search query if provided (search across name, phone, email, city)
            if search_query:
                leads = leads.filter(
                    Q(name__icontains=search_query) |
                    Q(phone__icontains=search_query) |
                    Q(email__icontains=search_query) |
                    Q(city__icontains=search_query)
                )

            # Pagination: Apply Django Paginator
            paginator = Paginator(leads, page_size)  # Set the number of items per page
            page = paginator.page(page_number)  # Get the specific page

            lead_list = await sync_to_async(list)(page.object_list)
            results = []

            for lead in lead_list:
                business_name = lead.business.business_name if lead.business else None

                results.append({
                    "date": lead.timestamp,
                    "name": lead.name,
                    "phone": lead.phone,
                    "email": lead.email,
                    "requirements": lead.interested,
                    "detail": lead.query,
                    "country": lead.country,
                    "city": lead.city,
                    "assigned": business_name,
                    "view": f"/leads/{lead.id}/view"
                })

            # Return paginated response
            return {
                "results": results,
                "totalPages": paginator.num_pages,
                "currentPage": page_number,
                "totalItems": paginator.count,
                "hasNext": page.has_next(),
                "hasPrevious": page.has_previous()
            }

        except Exception as e:
            #await MY_METHODS.printStatus(f"Error in GetLeadTiles: {e}")
            return None
    
