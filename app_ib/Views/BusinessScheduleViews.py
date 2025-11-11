from rest_framework.permissions import IsAuthenticated, AllowAny
from adrf.views import APIView as AsyncAPIView
from adrf.decorators import api_view

from app_ib.Controllers.BusinessSchedule.BusinessScheduleController import BUSINESS_SCHEDULE_CONTROLLER
from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.Names import NAMES
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.models import Business
from django.http import HttpRequest

class ProductView(AsyncAPIView):

    permission_classes = [IsAuthenticated]

    async def get(request: HttpRequest):
        try:
            business = request.user.user_business
            businessScheduleResponse = await BUSINESS_SCHEDULE_CONTROLLER.GetUserSchedule(business)
            return ServerResponse(
                response=businessScheduleResponse.response,
                message=businessScheduleResponse.message,
                code=businessScheduleResponse.code,
                data=businessScheduleResponse.data
            )
        except Exception as e:
            return ServerResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.business_fetch_error,
                code=RESPONSE_CODES.error,
                data={NAMES.ERROR:str(e)}
            )

    async def post(request: HttpRequest):
        try:
            business = request.user.user_business
            businessScheduleResponse = await BUSINESS_SCHEDULE_CONTROLLER.CreateOrUpdateBusinessSchedule(business, request.data)
            return ServerResponse(
                response=businessScheduleResponse.response,
                message=businessScheduleResponse.message,
                code=businessScheduleResponse.code,
                data=businessScheduleResponse.data
            )
        except Exception as e:
            return ServerResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.business_fetch_error,
                code=RESPONSE_CODES.error,
                data={NAMES.ERROR:str(e)}
            )
    async def put(request: HttpRequest):
        try:
            business = request.user.user_business
            businessScheduleResponse = await BUSINESS_SCHEDULE_CONTROLLER.UpdateBusinessSchedule(business, request.data)
            return ServerResponse(
                response=businessScheduleResponse.response,
                message=businessScheduleResponse.message,
                code=businessScheduleResponse.code,
                data=businessScheduleResponse.data
            )
        except Exception as e:
            return ServerResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.business_fetch_error,
                code=RESPONSE_CODES.error,
                data={NAMES.ERROR:str(e)}
            )