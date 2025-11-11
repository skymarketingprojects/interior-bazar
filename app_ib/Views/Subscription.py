from ast import Try
import httpx
import asyncio
from app_ib.Utils.MyMethods import MY_METHODS
from django.http import JsonResponse
from asgiref.sync import sync_to_async
from adrf.decorators import api_view
from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.Names import NAMES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from app_ib.Controllers.Subscription.SubscriptionController import SUBSCRIPTION_CONTROLLER


# @api_view(['POST'])
# async def CreateSubscriptionView(request):
#     try:
#         # Convert request.data to dot notation object
#         data = request.data

#         # Call Subscription Controller to Create Subscription
#         final_response = await asyncio.gather(SUBSCRIPTION_CONTROLLER.CreateSubscription(data=data))
#         final_response = final_response[0]

#         return ServerResponse(
#             response=final_response.response,
#             code=final_response.code,
#             message=final_response.message,
#             data=final_response.data
#         )

#     except Exception as e:
#         return ServerResponse(
#             response=RESPONSE_MESSAGES.error,
#             message=RESPONSE_MESSAGES.subscription_create_error,
#             code=RESPONSE_CODES.error,
#             data={NAMES.ERROR: str(e)}
#         )


# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# async def UpdateSubscriptionView(request):
#     try:
#         # Convert request.data to dot notation object
#         data =request.data

#         # Call Subscription Controller to Update Subscription
#         final_response = await asyncio.gather(SUBSCRIPTION_CONTROLLER.UpdateSubscription(data=data))
#         final_response = final_response[0]

#         return ServerResponse(
#             response=final_response.response,
#             code=final_response.code,
#             message=final_response.message,
#             data=final_response.data
#         )

#     except Exception as e:
#         return ServerResponse(
#             response=RESPONSE_MESSAGES.error,
#             message=RESPONSE_MESSAGES.subscription_update_error,
#             code=RESPONSE_CODES.error,
#             data={NAMES.ERROR: str(e)}
#         )


# @permission_classes([IsAuthenticated]) # put it below @api_view(['GET']) if using
@api_view(['GET'])
async def GetSubscriptionsView(request):
    try:
        # Fetch subscriptions using Subscription Controller
        final_response = await asyncio.gather(SUBSCRIPTION_CONTROLLER.GetSubscription())
        final_response = final_response[0]

        return ServerResponse(
            response=final_response.response,
            code=final_response.code,
            message=final_response.message,
            data=final_response.data
        )

    except Exception as e:
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.subscription_fetch_error,
            code=RESPONSE_CODES.error,
            data={NAMES.ERROR: str(e)}
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
async def GetSubscriptionByIDView(request, id):
    try:
        # Fetch subscription details by ID using Subscription Controller
        final_response = await asyncio.gather(SUBSCRIPTION_CONTROLLER.GetSubscriptionById(id=id))
        final_response = final_response[0]

        return ServerResponse(
            response=final_response.response,
            code=final_response.code,
            message=final_response.message,
            data=final_response.data
        )

    except Exception as e:
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.subscription_fetch_error,
            code=RESPONSE_CODES.error,
            data={NAMES.ERROR: str(e)}
        )
