from asgiref.sync import sync_to_async
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.LocalResponse import LocalResponse

from .Tasks.BusinessScheduleTasks import BUSINESS_SCHEDULE_TASKS
from .Validators.BusinessScheduleValidators import BUSINESS_SCHEDULE_VALIDATORS

from app_ib.models import Business, DaySchedule
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.Utils.Names import NAMES
class BUSINESS_SCHEDULE_CONTROLLER:
    @classmethod
    async def CreateOrUpdateBusinessSchedule(cls, user_ins, schedule_data):

        try:
            business_ins = user_ins
            
            day_map = {name: number for number, name in DaySchedule.DAYS_OF_WEEK}

            for day_name, values in schedule_data.items():
                day_number = day_map[day_name]
                await BUSINESS_SCHEDULE_TASKS.CreateOrUpdateDaySchedule(
                    business=business_ins,
                    day_number=day_number,
                    start_time=values.get(NAMES.START_TIME),
                    end_time=values.get(NAMES.END_TIME),
                    is_working=values.get(NAMES.IS_WORKING, False)
                )
            
            schedule_data = await BUSINESS_SCHEDULE_TASKS.GetScheduleByBusiness(business_ins)

            if not schedule_data:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message="Schedule not saved",
                    code=RESPONSE_CODES.not_exist,
                    data={}
                )

            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message="Schedule saved successfully",
                code=RESPONSE_CODES.success,
                data=schedule_data
            )

        except Exception as e:
            await MY_METHODS.printStatus(f"[CreateOrUpdateBusinessSchedule Error]: {e}")
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message="Failed to save schedule",
                code=RESPONSE_CODES.error,
                data={NAMES.ERROR: str(e)}
            )

    @classmethod
    async def GetBusinessSchedule(cls, user_ins):
        try:
            

            business_ins = user_ins
            schedule_data = await BUSINESS_SCHEDULE_TASKS.GetScheduleByBusiness(business_ins)

            if not schedule_data:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message="Schedule not found",
                    code=RESPONSE_CODES.not_exist,
                    data={}
                )

            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message="Schedule fetched successfully",
                code=RESPONSE_CODES.success,
                data=schedule_data
            )

        except Exception as e:
            await MY_METHODS.printStatus(f"[GetBusinessSchedule Error]: {e}")
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message="Failed to fetch schedule",
                code=RESPONSE_CODES.error,
                data={NAMES.ERROR: str(e)}
            )

    @classmethod
    async def UpdateBusinessSchedule(cls, user_ins, schedule_data):
        """
        Update an existing user's weekly schedule.
        schedule_data format:
        {
            "Monday": {NAMES.START_TIME: "09:00", NAMES.END_TIME: "10:00", NAMES.IS_WORKING: False},
            ...
        }
        """
        try:
            business_ins = user_ins

            update_resp = await BUSINESS_SCHEDULE_TASKS.UpdateUserSchedule(business_ins, schedule_data)
            if update_resp:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.success,
                    message="Schedule updated successfully",
                    code=RESPONSE_CODES.success,
                    data=update_resp
                )
            else:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message="Failed to update schedule",
                    code=RESPONSE_CODES.error,
                    data=update_resp
                )

        except Exception as e:
            await MY_METHODS.printStatus(f"[UpdateBusinessSchedule Error]: {e}")
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message="Error updating schedule",
                code=RESPONSE_CODES.error,
                data={NAMES.ERROR: str(e)}
            )