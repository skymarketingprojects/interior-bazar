from asgiref.sync import sync_to_async
from app_ib.models import Business, LeadQuery, BusinessPlan,CustomUser
from django.utils import timezone
from datetime import timedelta
from django.utils.dateparse import parse_datetime
from django.core.paginator import Paginator
from django.conf import settings
from app_ib.Utils.AppMode import APPMODE
from app_ib.decorators.ViewDecorator import taskExceptionHandler
from django.db.models import Count, Q, OuterRef, Subquery, QuerySet
from django.db.models.functions import Coalesce
from app_ib.Utils.MyMethods import MY_METHODS
from django.db.models import Value


class ADMIN_PANEL_TASKS:
    
    @classmethod
    @taskExceptionHandler
    async def GetTotalActiveBusinesses(cls):
        active_businesses = await sync_to_async(
            lambda: BusinessPlan.objects.filter(expireDate__gte=timezone.now()).values_list('business_id', flat=True).distinct().count()
        )()
        if active_businesses:
            return True,active_businesses
        return True,0
        
        
    @classmethod
    @taskExceptionHandler
    async def GetTotalInactiveBusinesses(cls):
        active_ids = await sync_to_async(
            lambda: list(BusinessPlan.objects.filter(expireDate__gte=timezone.now()).values_list('business_id', flat=True))
        )()
        inactive_count = await sync_to_async(
            lambda: Business.objects.exclude(id__in=active_ids).count()
        )()
        if inactive_count:
            return True,inactive_count
        return True,0
    
    @classmethod
    @taskExceptionHandler
    async def GetTotalBusinesses(cls):
        await MY_METHODS.printStatus(f'GetTotalBusinesses')
        count = 0
        if settings.ENV == APPMODE.PROD:
            count = await sync_to_async(lambda: Business.objects.filter(selfCreated=False).count())()
        else:
            count = await sync_to_async(lambda: Business.objects.all().count())()
        return True,count
    @classmethod
    @taskExceptionHandler
    async def GetWeeklySignups(cls):
        last_week = timezone.now() - timedelta(days=7)
        count = 0
        if settings.ENV == APPMODE.PROD:
            count = await sync_to_async(
                lambda: Business.objects.filter(timestamp__gte=last_week,selfCreated=False).count()
            )()
        else:
            count = await sync_to_async(
                lambda: Business.objects.filter(timestamp__gte=last_week).count()
            )()
        return True,count

    @classmethod
    @taskExceptionHandler
    async def GetBusinessTiles(cls, start_date=None, end_date=None, page_number=1, page_size=2):
        businesses = None
        if settings.ENV == APPMODE.PROD:
            businesses = Business.objects.filter(selfCreated=False).order_by('-timestamp')
        else:
            businesses = Business.objects.all().order_by('-timestamp')

        # Apply date filters if provided
        if start_date:
            start_date = parse_datetime(start_date)
            businesses = businesses.filter(timestamp__gte=start_date)
        if end_date:
            end_date = parse_datetime(end_date)
            businesses = businesses.filter(timestamp__lte=end_date)

        # Pagination: Apply Django Paginator
        paginator = Paginator(businesses, page_size)
        page = paginator.page(page_number)

        business_list:list[Business] = await sync_to_async(list)(page.object_list)
        results = []

        for business in business_list:
            business_id = business.pk

            # Latest plan for the business
            plan = await sync_to_async(
                lambda: BusinessPlan.objects.filter(business_id=business_id).order_by('-id').first()
            )()
            plan_name = plan.plan.title if plan else "No Plan"

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
                "name": business.businessName,
                "plan": plan_name,
                "assignedLead": assigned_leads_count,
                    "platformLead": platform_leads_count,
                "totalLeads": total_leads,
                "date": timezone.now().date()
            })

        # Return paginated response
        paginated_resp={
            "results": results,
            "totalPages": paginator.num_pages,
            "currentPage": page_number,
            "totalItems": paginator.count,
            'hasNext': page.has_next(),
            'hasPrevious': page.has_previous()
        }
        return True,paginated_resp

    @classmethod
    @taskExceptionHandler
    async def GetTotalUsers(cls):
        count = 0
        if settings.ENV == APPMODE.PROD:
            count = await sync_to_async(CustomUser.objects.filter(selfCreated=False).count)()
        else:
            count = await sync_to_async(CustomUser.objects.all().count)()
        return True,count



class ADMIN_PANEL_BUSINESS_TASKS_V2:

    @classmethod
    @taskExceptionHandler
    async def GetBusinessMetrics(cls, business_qs:QuerySet):

        now = timezone.now()
        last_week = now - timedelta(days=7)

        def _agg():
            return business_qs.aggregate(
                total=Count("id"),

                weekly_signup=Count(
                    "id",
                    filter=Q(timestamp__gte=last_week)
                ),

                active=Count(
                    "id",
                    filter=Q(
                        business_plan__expireDate__gte=now
                    )
                ),
            )

        data = await sync_to_async(_agg)()
        data["inactive"] = data["total"] - data["active"]

        return True, data


    @classmethod
    @taskExceptionHandler
    async def GetBusinessTiles(
        cls,
        business_qs: QuerySet,
        start_date=None,
        end_date=None,
        page_number=1,
        page_size=10
    ):
        if start_date:
            business_qs = business_qs.filter(timestamp__gte=parse_datetime(start_date))
        if end_date:
            business_qs = business_qs.filter(timestamp__lte=parse_datetime(end_date))

        latest_plan_sub = BusinessPlan.objects.filter(
            business_id=OuterRef("pk")
        ).order_by("-id").values("plan__title")[:1]

        annotated_qs = business_qs.annotate(
            latest_plan=Coalesce(Subquery(latest_plan_sub), Value("No Plan")),
            assigned_leads=Count(
                "business_lead_query",
                filter=Q(business_lead_query__business__isnull=False)
            )
        )

        paginator = Paginator(annotated_qs, page_size)
        page = await sync_to_async(paginator.page)(page_number)
        rows: list[Business] = await sync_to_async(list)(page.object_list)

        platform_leads:int = await sync_to_async(
            lambda: LeadQuery.objects.filter(business=None).count()
        )()

        results = [
            {
                "id": b.pk,
                "joinAt": b.timestamp,
                "name": b.businessName,
                "plan": b.latest_plan,
                "assignedLead": b.assigned_leads,
                "platformLead": platform_leads,
                "totalLeads": b.assigned_leads + platform_leads,
                "date": timezone.now().date()
            }
            for b in rows
        ]

        return True, {
            "results": results,
            "totalPages": paginator.num_pages,
            "currentPage": page_number,
            "totalItems": paginator.count,
            "hasNext": page.has_next(),
            "hasPrevious": page.has_previous()
        }


    @classmethod
    @taskExceptionHandler
    async def GetUserMetrics(cls, user_qs:QuerySet):

        def _agg():
            return user_qs.aggregate(total=Count("id"))

        return True, await sync_to_async(_agg)()
