from app_ib.models import CustomUser, Business, BusinessPlan
from collections import defaultdict
from asgiref.sync import sync_to_async
from django.utils import timezone
from django.db.models import Q, Count
from datetime import timedelta
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth
from app_ib.Utils.MyMethods import MY_METHODS
from django.conf import settings
from app_ib.Utils.AppMode import APPMODE

class ANALYTICS_TASKS:

    # 1. Total Clients
    @classmethod
    async def GetTotalClients(cls):
        try:
            clients_count = 0
            if settings.ENV == APPMODE.PROD:
                clients_count = await sync_to_async(
                    lambda: CustomUser.objects.filter(type="client", selfCreated=False).count()
                )()
            else:
                clients_count = await sync_to_async(
                    lambda: CustomUser.objects.filter(type="client").count()
                )()
            return clients_count
        except Exception as e:
            #await MY_METHODS.printStatus(f"Error in GetTotalClients: {e}")
            return None

    # 2. Total Business
    @classmethod
    async def GetTotalBusiness(cls):
        try:
            business_count = 0
            if settings.ENV == APPMODE.PROD:
                business_count = await sync_to_async(
                    lambda: Business.objects.filter(selfCreated=False).count()
                )()
            else:
                business_count = await sync_to_async(
                    lambda: Business.objects.all().count()
                )()
            return business_count
        except Exception as e:
            #await MY_METHODS.printStatus(f"Error in GetTotalBusiness: {e}")
            return None

    # 3. Total Users
    @classmethod
    async def GetTotalUsers(cls):
        try:
            users_count = 0
            if settings.ENV == APPMODE.PROD:
                users_count = await sync_to_async(
                    lambda: CustomUser.objects.filter(selfCreated=False).count()
                )()
            else:
                users_count = await sync_to_async(
                    lambda: CustomUser.objects.all().count()
                )()
            return users_count
        except Exception as e:
            #await MY_METHODS.printStatus(f"Error in GetTotalUsers: {e}")
            return None

    # 4. Today Signups (Clients / Business / Users)
    @classmethod
    async def GetTodaySignups(cls):
        try:
            today = timezone.now().date()

            clients_today = 0
            business_today = 0
            users_today = 0
            
            if settings.ENV == APPMODE.PROD:
                clients_today = await sync_to_async(
                    lambda: CustomUser.objects.filter(type="client", timestamp__date=today,selfCreated = False).count()
                )()
                business_today = await sync_to_async(
                    lambda: Business.objects.filter(timestamp__date=today,selfCreated = False).count()
                )()
                users_today = await sync_to_async(
                    lambda: CustomUser.objects.filter(timestamp__date=today,selfCreated = False).count()
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

            return {
                "clients": clients_today,
                "businesses": business_today,
                "users": users_today
            }
        except Exception as e:
            #await MY_METHODS.printStatus(f"Error in GetTodaySignups: {e}")
            return None
    @classmethod
    async def GetTodayUserSignups(cls):
        try:
            today = timezone.now().date()
            
            users_today = 0
            if settings.ENV == APPMODE.PROD:
                users_today = await sync_to_async(
                    lambda: CustomUser.objects.filter(timestamp__date=today,selfCreated = False).count()
                )()
            else:
                users_today = await sync_to_async(
                    lambda: CustomUser.objects.filter(timestamp__date=today).count()
                )()

            return users_today
        except Exception as e:
            #await MY_METHODS.printStatus(f"Error in GetTodaySignups: {e}")
            return None
    # 5. Business Active / Inactive (daily-weekly-monthly)
    @classmethod
    async def GetBusinessStatus(cls):
        try:
            now = timezone.now()

            def get_counts(start_date):
                active = 0
                inactive = 0
                if settings.ENV == APPMODE.PROD:
                    active = Business.objects.filter(
                        businessplan__is_active=True,
                        timestamp__gte=start_date,
                        selfCreated = False
                    ).count()
                    inactive = Business.objects.filter(
                        Q(businessplan__isnull=True) |
                        Q(businessplan__is_active=False),
                        timestamp__gte=start_date,
                        selfCreated = False
                    ).count()
                else:
                    active = Business.objects.filter(
                        businessplan__is_active=True,
                        timestamp__gte=start_date
                    ).count()
                    inactive = Business.objects.filter(
                        Q(businessplan__isnull=True) |
                        Q(businessplan__is_active=False),
                        timestamp__gte=start_date
                    ).count()
                return {"active": active, "inactive": inactive}

            data = {
                "daily": get_counts(now - timedelta(days=1)),
                "weekly": get_counts(now - timedelta(weeks=1)),
                "monthly": get_counts(now - timedelta(days=30)),
            }
            return data
        except Exception as e:
            #await MY_METHODS.printStatus(f"Error in GetBusinessStatus: {e}")
            return None

    # 6. Chart Data (generic function for clients, businesses, users)
    @classmethod
    async def GetChartData(cls, queryset, trunc_func, date_field="timestamp"):
        try:
            data = list(
                queryset.annotate(period=trunc_func(date_field))
                        .values("period")
                        .annotate(count=Count("id"))
                        .order_by("period")
            )
            if data:
                return data
            return []
        except Exception:
            return []

    @classmethod
    async def GetGroupedChartData(cls, model_map: dict, date_field="timestamp"):
        # #await MY_METHODS.printStatus("Entering GetGroupedChartData...")

        periods = {
            "daily": TruncDate,
            # "weekly": TruncWeek,
            # "monthly": TruncMonth,
        }

        results = {
            "daily": [],
            # "weekly": [],
            # "monthly": [],
        }

        for period_label, trunc_func in periods.items():
            # Use defaultdict to merge counts from multiple models by period
            period_counts = defaultdict(lambda: defaultdict(int))

            for model_label, queryset in model_map.items():
                data = await cls.GetChartData(queryset, trunc_func, date_field)
                for item in data:
                    # #await MY_METHODS.printStatus(f"[{model_label} - {period_label}]: {item}")
                    period_str = item["period"].isoformat()
                    period_counts[period_str][model_label] = item["count"]

            # Transform merged data into a list of dicts
            merged_data = []
            for period, counts in sorted(period_counts.items()):
                entry = {"date": period}
                for model_label in model_map.keys():
                    entry[model_label] = counts.get(model_label, 0)
                merged_data.append(entry)

            results[period_label] = merged_data

        # #await MY_METHODS.printStatus("Exiting GetGroupedChartData...")

        return results["daily"]
    # 6.a Chart for Clients
    @classmethod
    async def GetClientChart(cls):
        data = {"daily": [], "weekly": [], "monthly": []}
        if settings.ENV == APPMODE.PROD:
            data = await cls.GetChartData(CustomUser.objects.filter(type="client",selfCreated = False))
        else:
            data = await cls.GetChartData(CustomUser.objects.filter(type="client"))
        return data

    # 6.b Chart for Businesses
    @classmethod
    async def GetBusinessChart(cls):
        data = {"daily": [], "weekly": [], "monthly": []}
        if settings.ENV == APPMODE.PROD:
            data = await cls.GetChartData(Business.objects.filter(selfCreated = False))
        else:
            data = await cls.GetChartData(Business)
        return data
    # 6.c Chart for Users
    @classmethod
    async def GetUserChart(cls):
        data  = {"daily": [], "weekly": [], "monthly": []}
        if settings.ENV == APPMODE.PROD:
            data = await cls.GetChartData(CustomUser.objects.filter(selfCreated = False))
        else:
            data = await cls.GetChartData(CustomUser)
        return data

    @classmethod
    async def GetDailyUsersTask(cls):
        try:
            # Step 1: Query daily lead counts
            daily_counts = 0
            if settings.ENV == APPMODE.PROD:
                daily_counts = await sync_to_async(
                    lambda: list(
                        CustomUser.objects.filter(selfCreated = False)
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

            # Step 2: Build cumulative data
            cumulative = []
            total = 0
            for item in daily_counts:
                total += item['count']
                cumulative.append({
                    'date': item['date'].isoformat(),  # Make JSON serializable
                    'users': total
                })

            return cumulative

        except Exception as e:
            # Log or handle error if needed
            #await MY_METHODS.printStatus(f"Error in GetUsersDataTask: {e}")
            return None