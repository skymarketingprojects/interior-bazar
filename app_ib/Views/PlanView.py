import asyncio
from app_ib.Utils.MyMethods import MY_METHODS
from django.http import JsonResponse
from asgiref.sync import sync_to_async
from adrf.decorators import api_view
from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Controllers.Plans.PlanController import PLAN_CONTROLLER
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated


@api_view(['POST'])
@permission_classes([IsAuthenticated])
async def CreatePlanView(request):
    try:
        # Convert request.data to dot notation object
        user_ins= request.user
        data= request.POST.get('data')        
        payment_proof= request.FILES.get('attachment')
        data = MY_METHODS.json_to_object(data)
        
        # Call Auth Controller to Create User
        final_response = await  asyncio.gather(PLAN_CONTROLLER.CreatePlan(payment_proof=payment_proof,data=data,user_ins= user_ins))
        final_response = final_response[0]

        return ServerResponse(
            response=final_response.response,
            code=final_response.code,
            message=final_response.message,
            data=final_response.data)

    except Exception as e:
        # print(f'Error: {e}')
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.plan_create_error,
            code=RESPONSE_CODES.error,
            data={
                'error': str(e)
            })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
async def VerifyPaymentView(request):
    try:
        # Convert request.data to dot notation object
        data = MY_METHODS.json_to_object(request.data)
        # Call Auth Controller to Create User
        final_response = await  asyncio.gather(PLAN_CONTROLLER.VerifyPlan(data=data))
        final_response = final_response[0]

        return ServerResponse(
            response=final_response.response,
            code=final_response.code,
            message=final_response.message,
            data=final_response.data)

    except Exception as e:
        # print(f'Error: {e}')
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.plan_verify_errror,
            code=RESPONSE_CODES.error,
            data={
                'error': str(e)
            })
