from ast import Try
import httpx
import asyncio
from django.http import JsonResponse
from asgiref.sync import sync_to_async
from adrf.decorators import api_view
from types import SimpleNamespace
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.Utils.Names import NAMES
from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from app_ib.Controllers.Profile.ProfileController import PROFILE_CONTROLLER
from app_ib.Controllers.Plans.PlanController import PLAN_CONTROLLER
from app_ib.Controllers.Profile.Validators.ProfileValidators import (
    ProfileCreateOrUpdateSchema
)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
async def CreateProfileView(request):
    try:
        # Get user instance
        user_ins = request.user
        # Convert request.data to dot notation object
        # data = MY_METHODS.json_to_object(request.data)
        data = ProfileCreateOrUpdateSchema(**request.data)   
        # Call Auth Controller to Create User
        auth_resp = await PROFILE_CONTROLLER.CreateOrUpdateProfile(user_ins=user_ins, data=data)

        return ServerResponse(
            response=auth_resp.response,
            code=auth_resp.code,
            message=auth_resp.message,
            data=auth_resp.data)

    except Exception as e:
        # print(f'Error: {e}')
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.user_profile_create_error,
            code=RESPONSE_CODES.error,
            data={
                NAMES.ERROR: str(e).split('\n')[-1]
            })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
async def CreateOrUpdateProfileImageView(request):
    try:
        # Get user instance
        user_ins = request.user
        profile_image = request.FILES.get(NAMES.PROFILE_IMAGE_URL)     
        # Call Auth Controller to Create User
        auth_resp = await PROFILE_CONTROLLER.CreateOrUpdateProfileImage(
            user_ins=user_ins, profile_image=profile_image)

        return ServerResponse(
            response=auth_resp.response,
            code=auth_resp.code,
            message=auth_resp.message,
            data=auth_resp.data)

    except Exception as e:
        # print(f'Error: {e}')
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.user_profile_create_error,
            code=RESPONSE_CODES.error,
            data={
                NAMES.ERROR: str(e)
            })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
async def GetProfileView(request):
    try:
        # Get user instance
        userIns = request.user
        
        # Call Auth Controller to Create User
        auth_resp = await  asyncio.gather(PROFILE_CONTROLLER.GetProfile(userIns=userIns))
        auth_resp = auth_resp[0]

        return ServerResponse(
            response=auth_resp.response,
            code=auth_resp.code,
            message=auth_resp.message,
            data=auth_resp.data)

    except Exception as e:
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.user_profile_create_error,
            code=RESPONSE_CODES.error,
            data={
                NAMES.ERROR: str(e)
            })
@api_view(['GET'])
@permission_classes([IsAuthenticated])
async def GetProfileDashbordView(request):
    try:
        # Get user instance
        userIns = request.user
        
        # Call Auth Controller to Create User
        auth_resp = await  asyncio.gather(PROFILE_CONTROLLER.GetProfileDashbord(userIns=userIns))
        auth_resp = auth_resp[0]

        return ServerResponse(
            response=auth_resp.response,
            code=auth_resp.code,
            message=auth_resp.message,
            data=auth_resp.data)

    except Exception as e:
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.user_profile_create_error,
            code=RESPONSE_CODES.error,
            data={
                NAMES.ERROR: str(e)
            })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
async def GetPlanView(request):
    try:
        # Get user instance
        userIns = request.user
        
        # Call Auth Controller to Create User
        planData = await PLAN_CONTROLLER.GetBusinessPlan(user=userIns)
 

        return ServerResponse(
            response=planData.response,
            code=planData.code,
            message=planData.message,
            data=planData.data)

    except Exception as e:
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.user_profile_create_error,
            code=RESPONSE_CODES.error,
            data={
                NAMES.ERROR: str(e)
            }
        )