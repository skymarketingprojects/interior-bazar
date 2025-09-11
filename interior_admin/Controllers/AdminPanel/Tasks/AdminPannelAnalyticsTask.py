from app_ib.models import CustomUser, Business, BusinessPlan
from asgiref.sync import sync_to_async
from django.utils import timezone
from django.db.models import Q, Count
from datetime import timedelta
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth


class ANALYTICS_TASKS:

    # 1. Total Clients
    @classmethod
    async def GetTotalClients(cls):
        try:
            clients_count = await sync_to_async(
                lambda: CustomUser.objects.filter(type="client").count()
            )()
            return clients_count
        except Exception as e:
            print(f"Error in GetTotalClients: {e}")
            return None

    # 2. Total Business
    @classmethod
    async def GetTotalBusiness(cls):
        try:
            business_count = await sync_to_async(
                lambda: Business.objects.count()
            )()
            return business_count
        except Exception as e:
            print(f"Error in GetTotalBusiness: {e}")
            return None

    # 3. Total Users
    @classmethod
    async def GetTotalUsers(cls):
        try:
            users_count = await sync_to_async(
                lambda: CustomUser.objects.count()
            )()
            return users_count
        except Exception as e:
            print(f"Error in GetTotalUsers: {e}")
            return None

    # 4. Today Signups (Clients / Business / Users)
    @classmethod
    async def GetTodaySignups(cls):
        try:
            today = timezone.now().date()

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
            print(f"Error in GetTodaySignups: {e}")
            return None

    # 5. Business Active / Inactive (daily-weekly-monthly)
    @classmethod
    async def GetBusinessStatus(cls):
        try:
            now = timezone.now()

            def get_counts(start_date):
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
            print(f"Error in GetBusinessStatus: {e}")
            return None

    # 6. Chart Data (generic function for clients, businesses, users)
    @classmethod
    async def GetChartData(cls, model, date_field="timestamp"):
        try:
            def build_chart(qs, field):
                return list(
                    qs.annotate(period=field)
                      .values("period")
                      .annotate(count=Count("id"))
                      .order_by("period")
                )

            daily_qs = model.objects.all()
            weekly_qs = model.objects.all()
            monthly_qs = model.objects.all()

            data = {
                "daily": build_chart(daily_qs, TruncDate(date_field)),
                "weekly": build_chart(weekly_qs, TruncWeek(date_field)),
                "monthly": build_chart(monthly_qs, TruncMonth(date_field)),
            }
            return data
        except Exception as e:
            print(f"Error in GetChartData: {e}")
            return None

    # 6.a Chart for Clients
    @classmethod
    async def GetClientChart(cls):
        return await cls.GetChartData(CustomUser.objects.filter(type="client"))

    # 6.b Chart for Businesses
    @classmethod
    async def GetBusinessChart(cls):
        return await cls.GetChartData(Business)

    # 6.c Chart for Users
    @classmethod
    async def GetUserChart(cls):
        return await cls.GetChartData(CustomUser)
