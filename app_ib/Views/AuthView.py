
from asgiref.sync import async_to_sync
from adrf.decorators import api_view
from pydantic import ValidationError
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated

from app_ib.Controllers.Auth.AuthController import AUTH_CONTROLLER
from app_ib.Controllers.Auth.Validators.AuthValidators import (
    SignupValidator,
    LoginValidator,
    ForgotPasswordValidator,
    ChangePasswordValidator,
    ResetPasswordValidator,
    SendPhoneOtpValidator,
    VerifyPhoneOtpValidator,
    SendEmailOtpValidator,
    VerifyEmailOtpValidator,
)
from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.Names import NAMES


######################################
# Signup View
######################################
@api_view(['POST'])
def SignupView(request):
    try:
        data = SignupValidator(**request.data)

        auth_resp = async_to_sync(AUTH_CONTROLLER.SignupUser)(data=data, request=request)

        return ServerResponse(
            response=auth_resp.response,
            code=auth_resp.code,
            message=auth_resp.message,
            data=auth_resp.data,
        )

    except ValidationError as e:
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            code=RESPONSE_CODES.error,
            message="Invalid signup data",
            data=e.errors(),
        )


######################################
# Login View
######################################
@api_view(['POST'])
def LoginView(request):
    try:
        data = LoginValidator(**request.data)

        final_response = async_to_sync(AUTH_CONTROLLER.LoginUser)(data=data, request=request)

        return ServerResponse(
            response=final_response.response,
            code=final_response.code,
            message=final_response.message,
            data=final_response.data,
        )

    except ValidationError as e:
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            code=RESPONSE_CODES.error,
            message="Invalid login data",
            data=e.errors(),
        )


######################################
# Logout View
######################################
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def LogoutView(request):
    final_response = async_to_sync(
        AUTH_CONTROLLER.LogoutUser
    )(user_ins=request.user)

    return ServerResponse(
        response=final_response.response,
        code=final_response.code,
        message=final_response.message,
        data=final_response.data,
    )


######################################
# Delete Account View
######################################
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def DeleteAccountView(request):
    final_response = async_to_sync(
        AUTH_CONTROLLER.DeleteUser
    )(user_ins=request.user)

    return ServerResponse(
        response=final_response.response,
        code=final_response.code,
        message=final_response.message,
        data=final_response.data,
    )


######################################
# Send forgot password link
######################################
@api_view(['POST'])
def ForgotPasswordRequestView(request):
    try:
        data = ForgotPasswordValidator(**request.data)

        final_response = async_to_sync(
            AUTH_CONTROLLER.GenerateAndSendForgotPasswordLink
        )(data=data)

        return ServerResponse(
            response=final_response.response,
            code=final_response.code,
            message=final_response.message,
            data=final_response.data,
        )

    except ValidationError as e:
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            code=RESPONSE_CODES.error,
            message="Invalid request",
            data=e.errors(),
        )


######################################
# Verify forgot password link
######################################
@api_view(['GET'])
def ForgotPasswordView(request, hash):
    final_response = async_to_sync(
        AUTH_CONTROLLER.VerifyForgotPasswordLink
    )(hash=hash)

    return ServerResponse(
        response=final_response.response,
        code=final_response.code,
        message=final_response.message,
        data=final_response.data,
    )


######################################
# Change password (forgot-password flow)
######################################
@api_view(['POST'])
def ChnagePasswordView(request):
    try:
        data = ChangePasswordValidator(**request.data)

        final_response = async_to_sync(
            AUTH_CONTROLLER.ChanagePassword
        )(data=data)

        return ServerResponse(
            response=final_response.response,
            code=final_response.code,
            message=final_response.message,
            data=final_response.data,
        )

    except ValidationError as e:
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            code=RESPONSE_CODES.error,
            message="Invalid password data",
            data=e.errors(),
        )


######################################
# Reset Password (logged-in)
######################################
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ResetPasswordView(request):
    try:
        data = ResetPasswordValidator(**request.data)

        final_response = async_to_sync(
            AUTH_CONTROLLER.ResetPassword
        )(user_ins=request.user, data=data)

        return ServerResponse(
            response=final_response.response,
            code=final_response.code,
            message=final_response.message,
            data=final_response.data,
        )

    except ValidationError as e:
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            code=RESPONSE_CODES.error,
            message="Invalid reset password data",
            data=e.errors(),
        )


######################################
# Send Phone OTP
######################################
@api_view(['POST'])
def SendPhoneOtpView(request):
    try:
        data = SendPhoneOtpValidator(**request.data)

        final_response = async_to_sync(
            AUTH_CONTROLLER.SendPhoneOtp
        )(data=data)

        return ServerResponse(
            response=final_response.response,
            code=final_response.code,
            message=final_response.message,
            data=final_response.data,
        )

    except ValidationError as e:
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            code=RESPONSE_CODES.error,
            message="Invalid phone OTP request",
            data=e.errors(),
        )


######################################
# Verify Phone OTP
######################################
@api_view(['POST'])
def VerifyPhoneOtpView(request):
    try:
        data = VerifyPhoneOtpValidator(**request.data)

        final_response = async_to_sync(
            AUTH_CONTROLLER.VerifyPhoneOtp
        )(data=data, request=request)

        return ServerResponse(
            response=final_response.response,
            code=final_response.code,
            message=final_response.message,
            data=final_response.data,
        )

    except ValidationError as e:
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            code=RESPONSE_CODES.error,
            message="Invalid phone OTP verify request",
            data=e.errors(),
        )


######################################
# Send Email OTP
######################################
@api_view(['POST'])
def SendEmailOtpView(request):
    try:
        data = SendEmailOtpValidator(**request.data)

        final_response = async_to_sync(
            AUTH_CONTROLLER.SendEmailOtp
        )(data=data)

        return ServerResponse(
            response=final_response.response,
            code=final_response.code,
            message=final_response.message,
            data=final_response.data,
        )

    except ValidationError as e:
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            code=RESPONSE_CODES.error,
            message="Invalid email OTP request",
            data=e.errors(),
        )


######################################
# Verify Email OTP
######################################
@api_view(['POST'])
def VerifyEmailOtpView(request):
    try:
        data = VerifyEmailOtpValidator(**request.data)

        final_response = async_to_sync(
            AUTH_CONTROLLER.VerifyEmailOtp
        )(data=data, request=request)

        return ServerResponse(
            response=final_response.response,
            code=final_response.code,
            message=final_response.message,
            data=final_response.data,
        )

    except ValidationError as e:
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            code=RESPONSE_CODES.error,
            message="Invalid email OTP verify request",
            data=e.errors(),
        )
