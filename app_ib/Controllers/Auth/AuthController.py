# import base64
# import json
import random
import re
import logging
from django.conf import settings
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.Names import NAMES
from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.Utils.SafeCache import safe_cache
from app_ib.Controllers.Auth.Tasks.AuthTasks import AUTH_TASK
# from app_ib.Controllers.Auth.Validators.AuthValidators import AUTH_VALIDATOR
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.Utils.StaticValues import STATICVALUES
from interior_notification.Controllers.Publish import publishToUser

from app_ib.Controllers.Profile.ProfileController import PROFILE_CONTROLLER
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

logger = logging.getLogger(__name__)

OTP_TTL_SECONDS = 300
OTP_RESEND_THROTTLE_SECONDS = 60
OTP_MAX_ATTEMPTS = 5


def _check_otp(otp_key, code):
    """Shared OTP check for all verify endpoints. Returns an error
    LocalResponse, or None on match (the key is burned on match)."""
    cached = safe_cache.get(otp_key)
    if not cached:
        return LocalResponse(
            response=RESPONSE_MESSAGES.error,
            message="Code expired — request a new one",
            code=RESPONSE_CODES.not_exist,
            data={})

    if code != cached.get("code"):
        attempts = cached.get("attempts", 0) + 1
        if attempts >= OTP_MAX_ATTEMPTS:
            safe_cache.delete(otp_key)
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message="Too many attempts",
                code=RESPONSE_CODES.auth_error,
                data={})
        cached["attempts"] = attempts
        safe_cache.set(otp_key, cached, timeout=OTP_TTL_SECONDS)
        return LocalResponse(
            response=RESPONSE_MESSAGES.error,
            message="Incorrect code",
            code=RESPONSE_CODES.auth_error,
            data={})

    # Match — burn the code so it can't be replayed.
    safe_cache.delete(otp_key)
    return None


class AUTH_CONTROLLER:

    #####################################
    # Signup User
    #####################################
    @classmethod
    async def SignupUser(self, data:SignupValidator, request=None):
        try:
            response_data = {}

            # Validate Password
            # validate_password = await AUTH_VALIDATOR._validate_password(password=data.password)
            pass

            # if validate_password.code == RESPONSE_CODES.error:
            #     return LocalResponse(
            #         code=RESPONSE_CODES.error,
            #         response=RESPONSE_MESSAGES.error,
            #         message=validate_password.message,
            #         data=validate_password.data)

            # Check if user already exist 
            is_user_exist = await AUTH_TASK.IsUserExist(data.username)

            

            if is_user_exist:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.username_already_taken,
                    code=RESPONSE_CODES.already_exist,
                    data={})
            else:
                # Create User
                # user_ins = await AUTH_TASK.CreateUser(data.username, data.password, data.type)
                user_ins = await AUTH_TASK.CreateUser(
                    username=data.username,
                    password=data.password,
                    type=data.type,
                )
                pass

                if user_ins:
                    # Generate Token and build final response data
                    response_data = await AUTH_TASK.GenerateUserToken(user_ins, request=request)
                    pass

                else:
                    return LocalResponse(
                        response=RESPONSE_MESSAGES.error,
                        message=RESPONSE_MESSAGES.token_generate_error,
                        code=RESPONSE_CODES.error,
                    )
            
                # Success Response: 
                return LocalResponse(
                    response=RESPONSE_MESSAGES.success,
                    message=RESPONSE_MESSAGES.user_register_success,
                    code=RESPONSE_CODES.success,
                    data=response_data)

        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.user_register_error,
                code=RESPONSE_CODES.error,
                data=str(e))


    #####################################
    # Login User
    #####################################
    @classmethod
    async def LoginUser(self, data:LoginValidator, request=None):
        try:
            # Validate Password
            # validate_password = await AUTH_VALIDATOR._validate_password(password=data.password)
            pass
            # if validate_password.code == RESPONSE_CODES.error:
            #     return LocalResponse(
            #         code=RESPONSE_CODES.error,
            #         response=RESPONSE_MESSAGES.error,
            #         message=validate_password.message,
            #         data=validate_password.data)

            # Login User
            login_user = await AUTH_TASK.LoginUser(data.username, data.password)
            pass

            if login_user:
                # Generate Token and build final response data
                response_data = await AUTH_TASK.GenerateUserToken(login_user, request=request)
                pass
                userdata = await PROFILE_CONTROLLER.GetProfile(login_user)
                response_data['user'] = userdata.data

                

                return LocalResponse(
                    response=RESPONSE_MESSAGES.success,
                    message=RESPONSE_MESSAGES.user_login_success,
                    code=RESPONSE_CODES.success,
                    data=response_data)

            else:
                userExits = await AUTH_TASK.IsUserExist(data.username)
                if userExits:
                    return LocalResponse(
                        response=RESPONSE_MESSAGES.error,
                        message=RESPONSE_MESSAGES.incorrect_password,
                        code=RESPONSE_CODES.error,
                        data={})
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.incorrect_username,
                    code=RESPONSE_CODES.error,
                    data={})
        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.user_login_error,
                code=RESPONSE_CODES.error,
                data=str(e))

    #####################################
    # Logout User
    #####################################
    @classmethod
    async def LogoutUser(self, user_ins):
        try:
            logout_user = await AUTH_TASK.LogoutUser(user_ins)
            pass
            if logout_user:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.success,
                    message=RESPONSE_MESSAGES.user_logout_success,
                    code=RESPONSE_CODES.success,
                    data={})
        except:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.user_logout_error,
                code=RESPONSE_CODES.error,
                data={})

    #####################################
    # Delete User
    #####################################
    @classmethod
    async def DeleteUser(self, user_ins):
        try:
            delete_user = await AUTH_TASK.DeleteUser(user_ins)
            pass

            if delete_user:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.success,
                    message=RESPONSE_MESSAGES.user_removed_success,
                    code=RESPONSE_CODES.success,
                    data={})
        except:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.user_remove_error,
                code=RESPONSE_CODES.error,
                data={})

    #############################################
    # Generate and send forgot password link
    ##############################################
    @classmethod
    async def GenerateAndSendForgotPasswordLink(self, data:ForgotPasswordValidator):
        try:
            link = ""
            # Check if user exist
            is_user_exist = await AUTH_TASK.IsUserExist(username=data.username)
            pass
            
            timestamp= MY_METHODS.GetCurrentTimeinStr()

            if not is_user_exist:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.user_not_exist,
                    code=RESPONSE_CODES.error,
                    data={})

            if is_user_exist:
                # Generate and send forgot password link
                link= await AUTH_TASK.GenerateForgotPasswordLink(username=data.username,timestamp=timestamp)
                if(link):
                    pass

                    # Send Email
                    user_profile_data= await AUTH_TASK.GetUserProfileDataByUsername(username=data.username)
                    pass

                        # Send Email
                    if(user_profile_data):
                        is_email_sent = await AUTH_TASK.SendForgotPasswordEmail(user_profile_data=user_profile_data,link=link)
                        if(is_email_sent):                       
                            return LocalResponse(
                                response=RESPONSE_MESSAGES.success,
                                message=RESPONSE_MESSAGES.send_link_success,
                                code=RESPONSE_CODES.success,
                                data={
                                    NAMES.LINK:link,
                                })
                        else:
                            return LocalResponse(
                                response=RESPONSE_MESSAGES.success,
                                message=RESPONSE_MESSAGES.send_link_error,
                                code=RESPONSE_CODES.success,
                                data={
                                    NAMES.LINK:link,
                                })
                    else:
                        # No UserProfile (no email on file) — previously fell
                        # through and returned None, crashing the view with a 500
                        return LocalResponse(
                            response=RESPONSE_MESSAGES.error,
                            message=RESPONSE_MESSAGES.send_link_error,
                            code=RESPONSE_CODES.error,
                            data={})

                else:
                    return LocalResponse(
                        response=RESPONSE_MESSAGES.error,
                        message=RESPONSE_MESSAGES.generate_link_error,
                        code=RESPONSE_CODES.error,
                        data={})

        except:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.send_link_error,
                code=RESPONSE_CODES.error,
                data={})


    #####################################
    # Change Password
    #####################################
    @classmethod
    async def ChanagePassword(self,data):
        try:
            pass
            # if(data.password != data.confirm_password):
            #     return LocalResponse(
            #         response=RESPONSE_MESSAGES.error,
            #         message=RESPONSE_MESSAGES.password_not_match,
            #         code=RESPONSE_CODES.error,
            #         data={})

            # Validate Password
            # validate_password = await AUTH_VALIDATOR._validate_password(password=data.password)
            # # await MY_METHODS.printStatus(f'validate_password {validate_password}')

            # if validate_password.code == RESPONSE_CODES.error:
            #     return LocalResponse(
            #         code=RESPONSE_CODES.error,
            #         response=RESPONSE_MESSAGES.error,
            #         message=validate_password.message,
            #         data={})
        
            # Decode the hash and get time difference
            time_difference =  await AUTH_TASK.DecodeHashAndGetTimeDifference(hash=data.hash)
            if time_difference < STATICVALUES.PASSWORD_RESET_TIME_LIMIT:
                pass
                
                is_password_reset = await AUTH_TASK.ChangePassword(hash=data.hash, password=data.password)
                if is_password_reset:
                    return LocalResponse(
                        response=RESPONSE_MESSAGES.success,
                        message=RESPONSE_MESSAGES.password_reset_success,
                        code=RESPONSE_CODES.success,
                        data={})
                else:
                    return LocalResponse(
                        response=RESPONSE_MESSAGES.error,
                        message=RESPONSE_MESSAGES.password_reset_error,
                        code=RESPONSE_CODES.error,
                        data={})

        except Exception as e:
            pass
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.password_reset_error,
                code=RESPONSE_CODES.error,
                data={})

    #####################################
    # Verify Forgot Password Link
    #####################################
    @classmethod
    async def VerifyForgotPasswordLink(self,hash):
        try:
            pass
            time_difference =  await AUTH_TASK.DecodeHashAndGetTimeDifference(hash=hash)
            if time_difference > 59:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.link_expired_error,
                    code=RESPONSE_CODES.error,
                    data={
                        NAMES.TIME_DIFFERENCE:time_difference,
                    })
            data = {
                NAMES.KEY:hash,
                NAMES.EXPIRE_IN: (STATICVALUES.PASSWORD_RESET_TIME_LIMIT-time_difference),

            }
            
            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.default_success,
                code=RESPONSE_CODES.success,
                data=data)

        except Exception as e:
            pass
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.default_error,
                code=RESPONSE_CODES.error,
                data={})

    #####################################
    # Reset Password
    #####################################
    @classmethod
    async def ResetPassword(self, user_ins, data:ResetPasswordValidator):
        try:
            # Validate Password
            # validate_password = await AUTH_VALIDATOR._validate_password(password=data.password)
            # # await MY_METHODS.printStatus(f'validate_password')

            # if validate_password.code == RESPONSE_CODES.error:
            #     return LocalResponse(
            #         code=RESPONSE_CODES.error,
            #         response=RESPONSE_MESSAGES.error,
            #         message=validate_password.message,
            #         data={})
            
            # Reset Password
            is_password_reset = await AUTH_TASK.ResetPassword(user_ins=user_ins, data=data)
           
            if is_password_reset:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.success,
                    message=RESPONSE_MESSAGES.password_reset_success,
                    code=RESPONSE_CODES.success,
                    data={})
            else:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.password_reset_error,
                    code=RESPONSE_CODES.error,
                    data={})

        except:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.password_reset_error,
                code=RESPONSE_CODES.error,
                data={})

    #####################################
    # Send Phone OTP
    #####################################
    @classmethod
    async def SendPhoneOtp(self, data: SendPhoneOtpValidator):
        try:
            digits_cc = re.sub(r"[^\d]", "", data.countryCode or "91")
            normalized = MY_METHODS.formatPhoneInternational(data.phone, digits_cc)
            if not normalized:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message="Invalid phone number",
                    code=RESPONSE_CODES.bad_request,
                    data={})

            throttle_key = f"otp:phone:{normalized}:sent"
            if safe_cache.get(throttle_key):
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message="Please wait before requesting another code",
                    code=RESPONSE_CODES.bad_request,
                    data={})

            code = f"{random.randint(100000, 999999)}"
            otp_key = f"otp:phone:{normalized}"
            safe_cache.set(otp_key, {"code": code, "attempts": 0}, timeout=OTP_TTL_SECONDS)
            safe_cache.set(throttle_key, "1", timeout=OTP_RESEND_THROTTLE_SECONDS)

            response_data = {NAMES.EXPIRE_IN: OTP_TTL_SECONDS}

            if settings.MODE != "prod":
                # Dev: never hit SNS, hand the code back so the flow is testable.
                response_data["devCode"] = code
            else:
                message = f"Your Interior Bazzar verification code is {code}. Valid for 5 minutes."
                # ponytail: WhatsApp OTP needs a Meta-approved OTP template (WhatsappMessage
                # is locked to the "lead_query" template) — send SMS for both channels
                # until that template is approved.
                try:
                    sns_result = publishToUser(normalized, message)
                except Exception as e:
                    logger.exception("SendPhoneOtp: SNS publish raised for %s", normalized)
                    sns_result = None
                if sns_result is None:
                    return LocalResponse(
                        response=RESPONSE_MESSAGES.error,
                        message="Unable to send verification code",
                        code=RESPONSE_CODES.error,
                        data={})

            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message="Verification code sent",
                code=RESPONSE_CODES.success,
                data=response_data)

        except Exception as e:
            logger.exception('SendPhoneOtp failed')
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message="Unable to send verification code",
                code=RESPONSE_CODES.error,
                data={})

    #####################################
    # Verify Phone OTP
    #####################################
    @classmethod
    async def VerifyPhoneOtp(self, data: VerifyPhoneOtpValidator, request=None):
        try:
            digits_cc = re.sub(r"[^\d]", "", data.countryCode or "91")
            normalized = MY_METHODS.formatPhoneInternational(data.phone, digits_cc)
            if not normalized:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message="Invalid phone number",
                    code=RESPONSE_CODES.bad_request,
                    data={})

            otp_err = _check_otp(f"otp:phone:{normalized}", data.code)
            if otp_err:
                return otp_err

            user_ins, is_new_user = await AUTH_TASK.FindOrCreateOtpUser(
                username=normalized,
                profile_defaults={"phone": data.phone, "countryCode": f"+{digits_cc}"})

            if not user_ins:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.token_generate_error,
                    code=RESPONSE_CODES.error,
                    data={})

            # Password-login path (not RefreshToken.for_user) so sessions get recorded.
            response_data = await AUTH_TASK.GenerateUserToken(user_ins, request=request)
            userdata = await PROFILE_CONTROLLER.GetProfile(user_ins)
            response_data['user'] = userdata.data
            response_data['isNewUser'] = is_new_user

            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.user_login_success,
                code=RESPONSE_CODES.success,
                data=response_data)

        except Exception as e:
            logger.exception('VerifyPhoneOtp failed')
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message="Unable to verify code",
                code=RESPONSE_CODES.error,
                data={})

    #####################################
    # Send Email OTP
    #####################################
    @classmethod
    async def SendEmailOtp(self, data: SendEmailOtpValidator):
        try:
            normalized = data.email  # already lowercased by the validator

            throttle_key = f"otp:email:{normalized}:sent"
            if safe_cache.get(throttle_key):
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message="Please wait before requesting another code",
                    code=RESPONSE_CODES.bad_request,
                    data={})

            code = f"{random.randint(100000, 999999)}"
            otp_key = f"otp:email:{normalized}"
            safe_cache.set(otp_key, {"code": code, "attempts": 0}, timeout=OTP_TTL_SECONDS)
            safe_cache.set(throttle_key, "1", timeout=OTP_RESEND_THROTTLE_SECONDS)

            response_data = {NAMES.EXPIRE_IN: OTP_TTL_SECONDS}

            if settings.MODE != "prod":
                # Dev: skip SMTP, hand the code back so the flow is testable.
                response_data["devCode"] = code
            else:
                is_sent = await MY_METHODS.send_email(
                    email=normalized,
                    subject="Your Interior Bazzar verification code",
                    message=f"Your Interior Bazzar verification code is {code}. Valid for 5 minutes.",
                )
                if not is_sent:
                    return LocalResponse(
                        response=RESPONSE_MESSAGES.error,
                        message="Unable to send verification code",
                        code=RESPONSE_CODES.error,
                        data={})

            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message="Verification code sent",
                code=RESPONSE_CODES.success,
                data=response_data)

        except Exception as e:
            logger.exception('SendEmailOtp failed')
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message="Unable to send verification code",
                code=RESPONSE_CODES.error,
                data={})

    #####################################
    # Verify Email OTP
    #####################################
    @classmethod
    async def VerifyEmailOtp(self, data: VerifyEmailOtpValidator, request=None):
        try:
            normalized = data.email  # already lowercased by the validator

            otp_err = _check_otp(f"otp:email:{normalized}", data.code)
            if otp_err:
                return otp_err

            user_ins, is_new_user = await AUTH_TASK.FindOrCreateOtpUser(
                username=normalized, profile_defaults={"email": normalized})

            if not user_ins:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.token_generate_error,
                    code=RESPONSE_CODES.error,
                    data={})

            # Password-login path (not RefreshToken.for_user) so sessions get recorded.
            response_data = await AUTH_TASK.GenerateUserToken(user_ins, request=request)
            userdata = await PROFILE_CONTROLLER.GetProfile(user_ins)
            response_data['user'] = userdata.data
            response_data['isNewUser'] = is_new_user

            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.user_login_success,
                code=RESPONSE_CODES.success,
                data=response_data)

        except Exception as e:
            logger.exception('VerifyEmailOtp failed')
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message="Unable to verify code",
                code=RESPONSE_CODES.error,
                data={})

    #####################################
    # Send Password-Reset OTP (forgot-password step 1)
    #####################################
    @classmethod
    async def SendResetOtp(self, data: SendEmailOtpValidator):
        try:
            normalized = data.email  # already lowercased by the validator

            # Anti-enumeration: unknown accounts get the same 200 + generic
            # message, but no code is generated/cached/emailed.
            generic = LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message="If an account exists, a code has been sent",
                code=RESPONSE_CODES.success,
                data={NAMES.EXPIRE_IN: OTP_TTL_SECONDS})

            is_user_exist = await AUTH_TASK.IsUserExist(username=normalized)
            if not is_user_exist:
                return generic

            throttle_key = f"otp:reset:{normalized}:sent"
            if safe_cache.get(throttle_key):
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message="Please wait before requesting another code",
                    code=RESPONSE_CODES.bad_request,
                    data={})

            code = f"{random.randint(100000, 999999)}"
            safe_cache.set(f"otp:reset:{normalized}", {"code": code, "attempts": 0},
                           timeout=OTP_TTL_SECONDS)
            safe_cache.set(throttle_key, "1", timeout=OTP_RESEND_THROTTLE_SECONDS)

            if settings.MODE != "prod":
                # Dev: skip SMTP, hand the code back so the flow is testable.
                generic.data["devCode"] = code
            else:
                is_sent = await MY_METHODS.send_email(
                    email=normalized,
                    subject="Your Interior Bazzar verification code",
                    message=f"Your Interior Bazzar password reset code is {code}. Valid for 5 minutes.",
                )
                if not is_sent:
                    return LocalResponse(
                        response=RESPONSE_MESSAGES.error,
                        message="Unable to send verification code",
                        code=RESPONSE_CODES.error,
                        data={})

            return generic

        except Exception as e:
            logger.exception('SendResetOtp failed')
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message="Unable to send verification code",
                code=RESPONSE_CODES.error,
                data={})

    #####################################
    # Verify Password-Reset OTP (forgot-password step 2) — on match returns
    # the legacy base64 {username, timestamp} hash that change-password/
    # already accepts, so step 3 needs no new backend.
    #####################################
    @classmethod
    async def VerifyResetOtp(self, data: VerifyEmailOtpValidator):
        try:
            normalized = data.email  # already lowercased by the validator

            otp_err = _check_otp(f"otp:reset:{normalized}", data.code)
            if otp_err:
                return otp_err

            timestamp = MY_METHODS.GetCurrentTimeinStr()
            reset_hash = AUTH_TASK.BuildForgotPasswordHash(normalized, timestamp)

            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.default_success,
                code=RESPONSE_CODES.success,
                data={
                    NAMES.KEY: reset_hash,
                    NAMES.EXPIRE_IN: STATICVALUES.PASSWORD_RESET_TIME_LIMIT,
                })

        except Exception as e:
            logger.exception('VerifyResetOtp failed')
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message="Unable to verify code",
                code=RESPONSE_CODES.error,
                data={})