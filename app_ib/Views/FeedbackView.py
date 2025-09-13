import asyncio
from app_ib.Utils.MyMethods import MY_METHODS
from adrf.decorators import api_view
from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Controllers.Feedback.FeedbackController import FEEDBACK_CONTROLLER
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated

@api_view(['POST'])
@permission_classes([IsAuthenticated])
async def CreateFeedbackView(request):
    try:
        # Convert request.data to dot notation object
        data = MY_METHODS.json_to_object(request.data)
        user_ins=request.user
        # Call Auth Controller to Create User
        final_response = await  asyncio.gather(FEEDBACK_CONTROLLER.CreateFeedback(data=data,user_ins=user_ins))
        final_response = final_response[0]

        return ServerResponse(
            response=final_response.response,
            code=final_response.code,
            message=final_response.message,
            data=final_response.data)

    except Exception as e:
        # await MY_METHODS.printStatus(f'Error: {e}')
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.feedback_generate_error,
            code=RESPONSE_CODES.error,
            data={
                'error': str(e)
            })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
async def UpdateFeedbackStatusView(request):
    try:
        # Convert request.data to dot notation object
        data = MY_METHODS.json_to_object(request.data)
        
        # Call Auth Controller to Create User
        final_response = await  asyncio.gather(FEEDBACK_CONTROLLER.UpdateFeedbackStatus(data=data))
        final_response = final_response[0]

        return ServerResponse(
            response=final_response.response,
            code=final_response.code,
            message=final_response.message,
            data=final_response.data)

    except Exception as e:
        # await MY_METHODS.printStatus(f'Error: {e}')
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.feedback_generate_error,
            code=RESPONSE_CODES.error,
            data={
                'error': str(e)
            })