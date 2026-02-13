# import base64
# import json
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.Names import NAMES
from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.Controllers.Auth.Tasks.AuthTasks import AUTH_TASK
# from app_ib.Controllers.Auth.Validators.AuthValidators import AUTH_VALIDATOR
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.Utils.StaticValues import STATICVALUES

from app_ib.Controllers.Profile.ProfileController import PROFILE_CONTROLLER
from app_ib.Controllers.Auth.Validators.AuthValidators import (
    SignupValidator,
    LoginValidator,
    ForgotPasswordValidator,
    ChangePasswordValidator,
    ResetPasswordValidator,
)


class AUTH_CONTROLLER:

    #####################################
    # Signup User
    #####################################    
    @classmethod 
    async def SignupUser(self, data:SignupValidator):
        try:
            response_data = {}

            # Validate Password
            # validate_password = await AUTH_VALIDATOR._validate_password(password=data.password)
            # await MY_METHODS.printStatus(f'validate_password')

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
                    response=RESPONSE_MESSAGES.success,
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
                # await MY_METHODS.printStatus(f'Print username if user created {user_ins.username}')

                if user_ins:
                    # Generate Token and build final response data
                    response_data = await AUTH_TASK.GenerateUserToken(user_ins)
                    # await MY_METHODS.printStatus(f'response data {response_data}')

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
    async def LoginUser(self, data:LoginValidator):
        try:
            # Validate Password
            # validate_password = await AUTH_VALIDATOR._validate_password(password=data.password)
            # await MY_METHODS.printStatus(f'validate_password')
            # if validate_password.code == RESPONSE_CODES.error:
            #     return LocalResponse(
            #         code=RESPONSE_CODES.error,
            #         response=RESPONSE_MESSAGES.error,
            #         message=validate_password.message,
            #         data=validate_password.data)

            # Login User
            login_user = await AUTH_TASK.LoginUser(data.username, data.password)
            # await MY_METHODS.printStatus(f'login_user {login_user}')

            if login_user:
                # Generate Token and build final response data
                response_data = await AUTH_TASK.GenerateUserToken(login_user)
                # await MY_METHODS.printStatus(f'response data {response_data}')
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
            # await MY_METHODS.printStatus(f'logout_user {logout_user}')
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
            # await MY_METHODS.printStatus(f'delete_user {delete_user}')

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
            # await MY_METHODS.printStatus(f'is user exist {is_user_exist}')
            
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
                    # await MY_METHODS.printStatus(f'link {link}')

                    # Send Email
                    user_profile_data= await AUTH_TASK.GetUserProfileDataByUsername(username=data.username)
                    # await MY_METHODS.printStatus(f'user_profile_data {user_profile_data}')

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
            # await MY_METHODS.printStatus(f'data {data}')
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
                # await MY_METHODS.printStatus(f'time_difference {time_difference}')
                
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
            # await MY_METHODS.printStatus(f'Error: {e}')
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
            # await MY_METHODS.printStatus(f'hash {hash}')
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
            # await MY_METHODS.printStatus(f'Error: {e}')
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