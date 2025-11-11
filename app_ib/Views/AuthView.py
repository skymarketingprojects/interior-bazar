import asyncio
from django.http import JsonResponse
from asgiref.sync import sync_to_async
from adrf.decorators import api_view
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.Controllers.Auth.AuthController import AUTH_CONTROLLER
from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.Names import NAMES
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated

######################################
# Signup View
######################################
@api_view(['POST'])
async def SignupView(request):
    try:
        # Convert request.data to dot notation object
        data = MY_METHODS.json_to_object(request.data)

        # Call Auth Controller to Create User
        auth_resp = await  asyncio.gather(AUTH_CONTROLLER.SignupUser(data=data))
        auth_resp = auth_resp[0]

        return ServerResponse(
            response=auth_resp.response,
            code=auth_resp.code,
            message=auth_resp.message,
            data=auth_resp.data)

    except Exception as e:
        # #await MY_METHODS.printStatus(f'Error: {e}')
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.user_register_error,
            code=RESPONSE_CODES.error,
            data={
                NAMES.ERROR: str(e)
            })

######################################
# Login View
######################################
@api_view(['POST'])
async def LoginView(request):
    try:
        # Convert request.data to dot notation object
        data = MY_METHODS.json_to_object(request.data)

        # Call Auth Controller to Create User
        final_response = await  asyncio.gather(AUTH_CONTROLLER.LoginUser(data=data))
        final_response = final_response[0]

        return ServerResponse(
            response=final_response.response,
            code=final_response.code,
            message=final_response.message,
            data=final_response.data)

    except Exception as e:
        # #await MY_METHODS.printStatus(f'Error: {e}')
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.user_login_error,
            code=RESPONSE_CODES.error,
            data={
                NAMES.ERROR: str(e)
            })

######################################
# Logout View
######################################
@api_view(['POST'])
@permission_classes([IsAuthenticated])
async def LogoutView(request):
    try:
        user_ins = request.user
        #await MY_METHODS.printStatus(f'user_ins',user_ins)

        # Call Auth Controller to Create User
        final_response = await  asyncio.gather(AUTH_CONTROLLER.LogoutUser(user_ins=user_ins))
        final_response = final_response[0]

        return ServerResponse(
            response=final_response.response,
            code=final_response.code,
            message=final_response.message,
            data=final_response.data)

    except Exception as e:
        # #await MY_METHODS.printStatus(f'Error: {e}')
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.user_login_error,
            code=RESPONSE_CODES.error,
            data={
                NAMES.ERROR: str(e)
            })

######################################
# Delete Account View
######################################
@api_view(['POST'])
@permission_classes([IsAuthenticated])
async def DeleteAccountView(request):
    try:
        user_ins = request.user
        #await MY_METHODS.printStatus(f'user_ins',user_ins)

        # Call Auth Controller to Create User
        final_response = await  asyncio.gather(AUTH_CONTROLLER.DeleteUser(user_ins=user_ins))
        final_response = final_response[0]

        return ServerResponse(
            response=final_response.response,
            code=final_response.code,
            message=final_response.message,
            data=final_response.data)

    except Exception as e:
        # #await MY_METHODS.printStatus(f'Error: {e}')
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.user_login_error,
            code=RESPONSE_CODES.error,
            data={
                NAMES.ERROR: str(e)
            })

######################################
# Send forgot password link to mail
######################################
@api_view(['POST'])
async def ForgotPasswordRequestView(request):
    try:
        # Convert request.data to dot notation object
        data = MY_METHODS.json_to_object(request.data)

        # Call Auth Controller to Create User
        final_response = await  asyncio.gather(AUTH_CONTROLLER.GenerateAndSendForgotPasswordLink(data=data))
        final_response = final_response[0]
        #await MY_METHODS.printStatus(f'final_response {final_response}')
        return ServerResponse(
            response=final_response.response,
            code=final_response.code,
            message=final_response.message,
            data=final_response.data)

    except Exception as e:
        # #await MY_METHODS.printStatus(f'Error: {e}')
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.user_login_error,
            code=RESPONSE_CODES.error,
            data={
                NAMES.ERROR: str(e)
            })

######################################
# Verify forgot password link
######################################
@api_view(['GET'])
async def ForgotPasswordView(request,hash):
    try:
        final_response= await asyncio.gather(AUTH_CONTROLLER.VerifyForgotPasswordLink(hash=hash))
        final_response = final_response[0]
        #await MY_METHODS.printStatus(f'final_response {final_response}')
       
        return ServerResponse(
            response=final_response.response,
            code=final_response.code,
            message=final_response.message,
            data=final_response.data)

    except Exception as e:
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.user_login_error,
            code=RESPONSE_CODES.error,
            data={
                NAMES.ERROR: str(e)
            })

######################################
# Change password
######################################
@api_view(['POST'])
async def ChnagePasswordView(request):
    try:
        # Convert request.data to dot notation object
        data = MY_METHODS.json_to_object(request.data)

        # Call Auth Controller to Create User
        final_response = await  asyncio.gather(AUTH_CONTROLLER.ChanagePassword(data=data))
        final_response = final_response[0]
        #await MY_METHODS.printStatus(f'final_response {final_response}')

        return ServerResponse(
            response=final_response.response,
            code=final_response.code,
            message=final_response.message,
            data=final_response.data)

    except Exception as e:
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.user_login_error,
            code=RESPONSE_CODES.error,
            data={
                NAMES.ERROR: str(e)
            })

######################################
# Password Reset View
######################################
@api_view(['POST'])
@permission_classes([IsAuthenticated])
async def ResetPasswordView(request):
    try:
        # Convert request.data to dot notation object
        data = MY_METHODS.json_to_object(request.data)

        user_ins = request.user

        # Call Auth Controller to Create User
        final_response = await  asyncio.gather(AUTH_CONTROLLER.ResetPassword(user_ins= user_ins, data=data))
        final_response = final_response[0]
        #await MY_METHODS.printStatus(f'final_response {final_response}')

        return ServerResponse(
            response=final_response.response,
            code=final_response.code,
            message=final_response.message,
            data=final_response.data)

    except Exception as e:
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.user_login_error,
            code=RESPONSE_CODES.error,
            data={
                NAMES.ERROR: str(e)
            })

