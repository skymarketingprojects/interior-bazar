from asgiref.sync import sync_to_async
from app_ib.models import Business, DaySchedule
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.Utils.Names import NAMES
class BUSINESS_SCHEDULE_TASKS:

    @classmethod
    async def CreateOrUpdateDaySchedule(cls, business:Business, day_number, start_time, end_time, is_working):
        try:
            await MY_METHODS.printStatus(f"day - {day_number}\n start_time - {start_time}\n end_time - {end_time}\n is_working - {is_working}")
            # update_or_create logic
            await sync_to_async(DaySchedule.objects.update_or_create)(
                business=business,
                day=day_number,
                defaults={
                    "start_time": start_time,
                    "end_time": end_time,
                    "is_working": is_working
                }
            )

            data = await cls.GetScheduleByBusiness(business)
            return data
        except Exception as e:
            await MY_METHODS.printStatus(f'Error in CreateOrUpdateDaySchedule {e}')
            return None

    @classmethod
    async def GetScheduleByBusiness(cls, business:Business):
        try:
            schedules = await sync_to_async(list)(DaySchedule.objects.filter(business=business))
            result = {}
            for day in schedules:
                result[day.get_day_display()] = {
                    NAMES.START_TIME: day.start_time.strftime(NAMES.HM_FORMAT),
                    NAMES.END_TIME: day.end_time.strftime(NAMES.HM_FORMAT),
                    NAMES.IS_WORKING: day.is_working
                }
            return result
        except Exception as e:
            await MY_METHODS.printStatus(f'Error in GetScheduleByBusiness {e}')
            return None

    @classmethod
    async def UpdateUserSchedule(cls, business_ins, schedule_data):
       
        try:
            day_map = {name: number for number, name in DaySchedule.DAYS_OF_WEEK}

            for day_name, values in schedule_data.items():
                day_number = day_map[day_name]

                # Fetch existing schedule for that day
                is_schedule_exist = await sync_to_async(
                    DaySchedule.objects.filter(business=business_ins, day=day_number).exists
                )()

                if is_schedule_exist:
                    schedule_ins = await sync_to_async(
                        DaySchedule.objects.get
                    )(business=business_ins, day=day_number)

                    schedule_ins.start_time = values.get(NAMES.START_TIME)
                    schedule_ins.end_time = values.get(NAMES.END_TIME)
                    schedule_ins.is_working = values.get(NAMES.IS_WORKING, False)
                    await sync_to_async(schedule_ins.save)()
            data = cls.GetScheduleByBusiness(business_ins)

            return data

        except Exception as e:
            await MY_METHODS.printStatus(f'Error in UpdateUserSchedule {e}')
            return None