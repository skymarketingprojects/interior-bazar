from app_ib.models import CustomUser, Business, BusinessPlan, LeadQuery
from collections import defaultdict
from asgiref.sync import sync_to_async
from django.utils import timezone
from django.db.models import Q, Count,QuerySet
from datetime import timedelta
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth
from django.conf import settings
from app_ib.Utils.AppMode import APPMODE
from app_ib.decorators.ViewDecorator import taskExceptionHandler


class ANALYTICS_TASKS:

    # 1. Total Clients
    @classmethod
    @taskExceptionHandler
    async def GetTotalClients(cls):
        clients_count = 0
        if settings.ENV == APPMODE.PROD:
            clients_count = await sync_to_async(
                lambda: CustomUser.objects.filter(type="client", selfCreated=False).count()
            )()
        else:
            clients_count = await sync_to_async(
                lambda: CustomUser.objects.filter(type="client").count()
            )()
        return True, clients_count


    # 2. Total Business
    @classmethod
    @taskExceptionHandler
    async def GetTotalBusiness(cls):
        business_count = 0
        if settings.ENV == APPMODE.PROD:
            business_count = await sync_to_async(
                lambda: Business.objects.filter(selfCreated=False).count()
            )()
        else:
            business_count = await sync_to_async(
                lambda: Business.objects.all().count()
            )()
        return True, business_count


    # 3. Total Users
    @classmethod
    @taskExceptionHandler
    async def GetTotalUsers(cls):
        users_count = 0
        if settings.ENV == APPMODE.PROD:
            users_count = await sync_to_async(
                lambda: CustomUser.objects.filter(selfCreated=False).count()
            )()
        else:
            users_count = await sync_to_async(
                lambda: CustomUser.objects.all().count()
            )()
        return True, users_count


    # 4. Today Signups
    @classmethod
    @taskExceptionHandler
    async def GetTodaySignups(cls):
        today = timezone.now().date()

        clients_today = 0
        business_today = 0
        users_today = 0

        if settings.ENV == APPMODE.PROD:
            clients_today = await sync_to_async(
                lambda: CustomUser.objects.filter(type="client", timestamp__date=today, selfCreated=False).count()
            )()
            business_today = await sync_to_async(
                lambda: Business.objects.filter(timestamp__date=today, selfCreated=False).count()
            )()
            users_today = await sync_to_async(
                lambda: CustomUser.objects.filter(timestamp__date=today, selfCreated=False).count()
            )()
        else:
            clients_today = await sync_to_async(
                lambda: CustomUser.objects.filter(type="client", timestamp__date=today).count()
            )()
            business_today = await sync_to_async(
                lambda: Business.objects.filter(timestamp__date=today).count()
            )()
            users_today = await sync_to_async(
                lambda: CustomUser.objects.filter(timestamp__date=today).count()
            )()

        return True, {
            "clients": clients_today,
            "businesses": business_today,
            "users": users_today
        }


    @classmethod
    @taskExceptionHandler
    async def GetTodayUserSignups(cls):
        today = timezone.now().date()

        users_today = 0
        if settings.ENV == APPMODE.PROD:
            users_today = await sync_to_async(
                lambda: CustomUser.objects.filter(timestamp__date=today, selfCreated=False).count()
            )()
        else:
            users_today = await sync_to_async(
                lambda: CustomUser.objects.filter(timestamp__date=today).count()
            )()

        return True, users_today


    # 5. Business Active / Inactive
    @classmethod
    @taskExceptionHandler
    async def GetBusinessStatus(cls):
        now = timezone.now()

        def get_counts(start_date):
            active = 0
            inactive = 0
            if settings.ENV == APPMODE.PROD:
                active = Business.objects.filter(
                    businessplan__isActive=True,
                    timestamp__gte=start_date,
                    selfCreated=False
                ).count()
                inactive = Business.objects.filter(
                    Q(businessplan__isnull=True) |
                    Q(businessplan__isActive=False),
                    timestamp__gte=start_date,
                    selfCreated=False
                ).count()
            else:
                active = Business.objects.filter(
                    businessplan__isActive=True,
                    timestamp__gte=start_date
                ).count()
                inactive = Business.objects.filter(
                    Q(businessplan__isnull=True) |
                    Q(businessplan__isActive=False),
                    timestamp__gte=start_date
                ).count()
            return {"active": active, "inactive": inactive}

        data = {
            "daily": get_counts(now - timedelta(days=1)),
            "weekly": get_counts(now - timedelta(weeks=1)),
            "monthly": get_counts(now - timedelta(days=30)),
        }

        return True, data


    # 6. Chart Data
    @classmethod
    @taskExceptionHandler
    async def GetChartData(cls, queryset, trunc_func, date_field="timestamp"):
        data = list(
            queryset.annotate(period=trunc_func(date_field))
                    .values("period")
                    .annotate(count=Count("id"))
                    .order_by("period")
        )
        if data:
            return True, data
        return True, []


    @classmethod
    @taskExceptionHandler
    async def GetGroupedChartData(cls, model_map: dict, date_field="timestamp"):

        periods = {
            "daily": TruncDate,
        }

        results = {
            "daily": [],
        }

        for period_label, trunc_func in periods.items():

            period_counts = defaultdict(lambda: defaultdict(int))

            for model_label, queryset in model_map.items():
                status, data = await cls.GetChartData(queryset, trunc_func, date_field)

                for item in data:
                    period_str = item["period"].isoformat()
                    period_counts[period_str][model_label] = item["count"]

            merged_data = []
            for period, counts in sorted(period_counts.items()):
                entry = {"date": period}
                for model_label in model_map.keys():
                    entry[model_label] = counts.get(model_label, 0)
                merged_data.append(entry)

            results[period_label] = merged_data

        return True, results["daily"]


    @classmethod
    @taskExceptionHandler
    async def GetClientChart(cls):
        if settings.ENV == APPMODE.PROD:
            status, data = await cls.GetChartData(
                CustomUser.objects.filter(type="client", selfCreated=False),
                TruncDate
            )
        else:
            status, data = await cls.GetChartData(
                CustomUser.objects.filter(type="client"),
                TruncDate
            )
        return True, data


    @classmethod
    @taskExceptionHandler
    async def GetBusinessChart(cls):
        if settings.ENV == APPMODE.PROD:
            status, data = await cls.GetChartData(
                Business.objects.filter(selfCreated=False),
                TruncDate
            )
        else:
            status, data = await cls.GetChartData(
                Business.objects.all(),
                TruncDate
            )
        return True, data


    @classmethod
    @taskExceptionHandler
    async def GetUserChart(cls):
        if settings.ENV == APPMODE.PROD:
            status, data = await cls.GetChartData(
                CustomUser.objects.filter(selfCreated=False),
                TruncDate
            )
        else:
            status, data = await cls.GetChartData(
                CustomUser.objects.all(),
                TruncDate
            )
        return True, data


    @classmethod
    @taskExceptionHandler
    async def GetDailyUsersTask(cls):

        daily_counts = 0
        if settings.ENV == APPMODE.PROD:
            daily_counts = await sync_to_async(
                lambda: list(
                    CustomUser.objects.filter(selfCreated=False)
                    .annotate(date=TruncDate('timestamp'))
                    .values('date')
                    .annotate(count=Count('id'))
                    .order_by('date')
                )
            )()
        else:
            daily_counts = await sync_to_async(
                lambda: list(
                    CustomUser.objects
                    .annotate(date=TruncDate('timestamp'))
                    .values('date')
                    .annotate(count=Count('id'))
                    .order_by('date')
                )
            )()

        cumulative = []
        total = 0
        for item in daily_counts:
            total += item['count']
            cumulative.append({
                'date': item['date'].isoformat(),
                'users': total
            })

        return True, cumulative


class ADMIN_ANALYTICS_TASKS_V2:

    @classmethod
    @taskExceptionHandler
    async def GetSystemTotals(
        cls,
        user_qs:QuerySet,
        client_qs:QuerySet,
        business_qs:QuerySet
    ):

        def _calc():
            return {
                "users": user_qs.count(),
                "clients": client_qs.count(),
                "business": business_qs.count()
            }

        return True, await sync_to_async(_calc)()


    @classmethod
    @taskExceptionHandler
    async def GetTodayTotals(
        cls,
        user_qs:QuerySet,
        client_qs:QuerySet,
        business_qs:QuerySet
    ):

        today = timezone.now().date()

        def _calc():
            return {
                "users": user_qs.filter(timestamp__date=today).count(),
                "clients": client_qs.filter(timestamp__date=today).count(),
                "business": business_qs.filter(timestamp__date=today).count()
            }

        return True, await sync_to_async(_calc)()


    @classmethod
    @taskExceptionHandler
    async def GetBusinessStatus(cls, business_qs:QuerySet):

        now = timezone.now()

        def _agg(start_date):
            qs = business_qs.filter(timestamp__gte=start_date)

            return qs.aggregate(
                active=Count(
                    "id",
                    filter=Q(businessplan__isActive=True)
                ),
                inactive=Count(
                    "id",
                    filter=(
                        Q(businessplan__isnull=True) |
                        Q(businessplan__isActive=False)
                    )
                )
            )

        return True, {
            "daily": await sync_to_async(_agg)(now - timedelta(days=1)),
            "weekly": await sync_to_async(_agg)(now - timedelta(days=7)),
            "monthly": await sync_to_async(_agg)(now - timedelta(days=30)),
        }


    @classmethod
    @taskExceptionHandler
    async def GetGroupedChartData(cls, model_map: dict[str, QuerySet]):

        def _calc():

            period_counts = defaultdict(lambda: defaultdict(int))
            all_labels = list(model_map.keys())

            for label, qs in model_map.items():
                rows = list(
                    qs.annotate(date=TruncDate("timestamp"))
                    .values("date")
                    .annotate(count=Count("id"))
                    .order_by("date")
                )

                for r in rows:
                    period_counts[r["date"].isoformat()][label] = r["count"]

            result = []
            for date, counts in sorted(period_counts.items()):
                entry = {"date": date}

                # Ensure ALL labels exist for every date
                for label in all_labels:
                    entry[label] = counts.get(label, 0)

                result.append(entry)

            return result

        return True, await sync_to_async(_calc)()


    @classmethod
    @taskExceptionHandler
    async def GetLeadAnalyticsData(cls, lead_qs: QuerySet):
        def _calc():
            def normalize(val):
                if not val: return "Unknown"
                return str(val).strip().title()

            period_data = defaultdict(lambda: {
                "totalLeads": 0,
                "newLeads": 0,
                "assignedLeads": 0,
                "tags": defaultdict(int),
                "stages": defaultdict(int),
                "leadStatuses": defaultdict(int),
                "statuses": defaultdict(int)
            })

            rows = list(
                lead_qs.annotate(date=TruncDate("timestamp"))
                .values(
                    "date", "status", "leadStatus", "stage", "tag", "business"
                )
                .order_by("date")
            )

            for r in rows:
                date_str = r["date"].isoformat()
                day_stats = period_data[date_str]

                day_stats["totalLeads"] += 1
                
                # New leads logic (status normalized to 'New')
                if normalize(r["status"]) == "New":
                    day_stats["newLeads"] += 1
                
                # Assigned leads logic (business is not None)
                if r["business"] is not None:
                    day_stats["assignedLeads"] += 1

                # Group categorical fields
                day_stats["tags"][normalize(r["tag"] or "No Tag")] += 1
                day_stats["stages"][normalize(r["stage"] or "No Stage")] += 1
                day_stats["leadStatuses"][normalize(r["leadStatus"] or "No Lead Status")] += 1
                day_stats["statuses"][normalize(r["status"] or "No Status")] += 1

            # Convert defaultdicts to regular dicts for JSON serialization
            result = []
            for date, stats in sorted(period_data.items()):
                result.append({
                    "date": date,
                    "totalLeads": stats["totalLeads"],
                    "newLeads": stats["newLeads"],
                    "assignedLeads": stats["assignedLeads"],
                    "tags": dict(stats["tags"]),
                    "stages": dict(stats["stages"]),
                    "leadStatuses": dict(stats["leadStatuses"]),
                    "statuses": dict(stats["statuses"])
                })
            return result

        return True, await sync_to_async(_calc)()
