from app_ib.models import LeadQuery, PlanQuery
from asgiref.sync import sync_to_async
from django.utils import timezone
from datetime import timedelta
from django.utils.dateparse import parse_datetime
from django.core.paginator import Paginator
from django.db.models import Q,Count
from app_ib.decorators.ViewDecorator import taskExceptionHandler
from django.db.models import QuerySet

class LEAD_TASKS:

    @classmethod
    @taskExceptionHandler
    async def GetTotalAssignedLeads(cls):
        assignedLeads = await sync_to_async(
            lambda: LeadQuery.objects.filter(business__isnull=False).count()
        )()
        return True, assignedLeads


    @classmethod
    @taskExceptionHandler
    async def GetPlatformLeads(cls):
        platformLeadsCount = await sync_to_async(
            lambda: PlanQuery.objects.count()
        )()
        return True, platformLeadsCount


    @classmethod
    @taskExceptionHandler
    async def GetTotalUnassignedLeads(cls):
        unassignedCount = await sync_to_async(
            lambda: LeadQuery.objects.filter(business__isnull=True).count()
        )()
        return True, unassignedCount


    @classmethod
    @taskExceptionHandler
    async def GetTotalLeads(cls):
        status1, unassignedLeads = await cls.GetTotalUnassignedLeads()
        status2, assignedLeads = await cls.GetTotalAssignedLeads()
        status3, platformLeads = await cls.GetPlatformLeads()

        total = (unassignedLeads or 0) + (assignedLeads or 0) + (platformLeads or 0)
        return True, total


    @classmethod
    @taskExceptionHandler
    async def GetTodayLeads(cls):
        today = timezone.now().date()
        todayLeads = await sync_to_async(
            lambda: LeadQuery.objects.filter(timestamp__date=today).count()
        )()
        return True, todayLeads


    @classmethod
    @taskExceptionHandler
    async def GetLeadTiles(cls, start_date=None, end_date=None, search_query=None, page_number=1, page_size=10):

        leads = LeadQuery.objects.all()

        # Date filters
        if start_date:
            start_date = parse_datetime(start_date)
            leads = leads.filter(timestamp__gte=start_date)

        if end_date:
            end_date = parse_datetime(end_date)
            leads = leads.filter(timestamp__lte=end_date)

        # Search filter
        if search_query:
            leads = leads.filter(
                Q(name__icontains=search_query) |
                Q(phone__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(city__icontains=search_query)
            )

        paginator = Paginator(leads, page_size)
        page = paginator.page(page_number)

        lead_list:list[LeadQuery] = await sync_to_async(list)(page.object_list)

        results = []
        for lead in lead_list:
            business_name = lead.business.businessName if lead.business else None
            results.append({
                "id": lead.id,
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

        paginated_response = {
            "results": results,
            "totalPages": paginator.num_pages,
            "currentPage": page_number,
            "totalItems": paginator.count,
            "hasNext": page.has_next(),
            "hasPrevious": page.has_previous()
        }

        return True, paginated_response


class ADMIN_PANEL_LEAD_TASKS_V2:

    @classmethod
    @taskExceptionHandler
    async def GetLeadMetrics(cls, lead_qs:QuerySet, plan_qs:QuerySet=None):

        today = timezone.now().date()

        def _agg():
            base = lead_qs.aggregate(
                totalLeads=Count("id"),

                assignedLeads=Count(
                    "id",
                    filter=Q(business__isnull=False)
                ),

                unassignedLeads=Count(
                    "id",
                    filter=Q(business__isnull=True)
                ),

                todayLeads=Count(
                    "id",
                    filter=Q(timestamp__date=today)
                ),
            )

            # Dynamic status counts
            status_counts = dict(
                lead_qs
                .values("status")
                .annotate(count=Count("id"))
                .values_list("status", "count")
            )
            admin_status = dict(
                lead_qs
                .values("leadStatus")
                .annotate(count=Count("id"))
                .values_list("leadStatus", "count")
            )
            stage_metrics = dict(
                lead_qs
                .values("stage")
                .annotate(count=Count("id"))
                .values_list("stage", "count")
            )
            category_metrics = dict(
                lead_qs
                .values("category")
                .annotate(count=Count("id"))
                .values_list("category", "count")
            )

            base["statusMetrics"] = status_counts
            base["adminStatusMetrics"] = admin_status
            base["stageMetrics"] = stage_metrics
            base["categoryMetrics"] = category_metrics

            if plan_qs is not None:
                base["platformLeads"] = plan_qs.count()
            else:
                base["platformLeads"] = 0

            base["finalTotal"] = base["totalLeads"] + base["platformLeads"]

            return base


        return True, await sync_to_async(_agg)()


    @classmethod
    @taskExceptionHandler
    async def GetLeadTiles(
        cls,
        lead_qs:QuerySet,
        start_date=None,
        end_date=None,
        search_query=None,
        page_number=1,
        page_size=10
    ):

        if start_date:
            lead_qs = lead_qs.filter(
                timestamp__gte=parse_datetime(start_date)
            )

        if end_date:
            lead_qs = lead_qs.filter(
                timestamp__lte=parse_datetime(end_date)
            )

        if search_query:
            lead_qs = lead_qs.filter(
                Q(name__icontains=search_query) |
                Q(phone__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(city__icontains=search_query)
            )

        paginator = Paginator(lead_qs.select_related("business"), page_size)
        page = await sync_to_async(paginator.page)(page_number)
        rows:list[LeadQuery] = await sync_to_async(list)(page.object_list)

        results = [
            {
                "id": l.id,
                "date": l.timestamp,
                "name": l.name,
                "phone": l.phone,
                "email": l.email,
                "requirements": l.interested,
                "detail": l.query,
                "country": l.country,
                "city": l.city,
                "assigned": l.business.businessName if l.business else None,
                "view": f"/leads/{l.id}/view"
            }
            for l in rows
        ]

        return True, {
            "results": results,
            "totalPages": paginator.num_pages,
            "currentPage": page_number,
            "totalItems": paginator.count,
            "hasNext": page.has_next(),
            "hasPrevious": page.has_previous()
        }
