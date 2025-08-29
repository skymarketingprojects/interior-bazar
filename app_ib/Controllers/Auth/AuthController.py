import base64
import json
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.Controllers.Auth.Tasks.AuthTasks import AUTH_TASK
from app_ib.Controllers.Auth.Validators.AuthValidators import AUTH_VALIDATOR
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.Utils.StaticValues import STATICVALUES


class AUTH_CONTROLLER:

    #####################################
    # Signup User
    #####################################    
    @classmethod 
    async def SignupUser(self, data):
        try:
            response_data = {}

            # Validate Password
            validate_password = await AUTH_VALIDATOR._validate_password(password=data.password)
            print(f'validate_password')

            if validate_password.code == RESPONSE_CODES.error:
                return LocalResponse(
                    code=RESPONSE_CODES.error,
                    response=RESPONSE_MESSAGES.error,
                    message=validate_password.message,
                    data={})

            # Check if user already exist 
            is_user_exist = await AUTH_TASK.IsUserExist(data.username)
            print(f'is user exist {is_user_exist}')
            
            if is_user_exist:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.success,
                    message=RESPONSE_MESSAGES.user_exist,
                    code=RESPONSE_CODES.success,
                    data={})
            else:
                # Create User
                user_ins = await AUTH_TASK.CreateUser(data.username, data.password, data.type)
                print(f'Print username if user created {user_ins.username}')

                if user_ins:
                    # Generate Token and build final response data
                    response_data = await AUTH_TASK.GenerateUserToken(user_ins)
                    print(f'response data {response_data}')

                else:
                    return LocalResponse(
                        response=RESPONSE_MESSAGES.error,
                        message=RESPONSE_MESSAGES.token_generate_error,
                        code=RESPONSE_CODES.error,
                        data={})
                
                # Success Response: 
                return LocalResponse(
                    response=RESPONSE_MESSAGES.success,
                    message=RESPONSE_MESSAGES.user_register_success,
                    code=RESPONSE_CODES.success,
                    data=response_data)

        except:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.user_register_error,
                code=RESPONSE_CODES.error,
                data={})


    #####################################
    # Login User
    #####################################
    @classmethod 
    async def LoginUser(self, data):
        try:
            # Validate Password
            validate_password = await AUTH_VALIDATOR._validate_password(password=data.password)
            print(f'validate_password')

            # Login User
            login_user = await AUTH_TASK.LoginUser(data.username, data.password)
            print(f'login_user {login_user}')

            if login_user:
                # Generate Token and build final response data
                response_data = await AUTH_TASK.GenerateUserToken(login_user)
                print(f'response data {response_data}')

                return LocalResponse(
                    response=RESPONSE_MESSAGES.success,
                    message=RESPONSE_MESSAGES.user_login_success,
                    code=RESPONSE_CODES.success,
                    data=response_data)

            else:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.user_login_error,
                    code=RESPONSE_CODES.error,
                    data={})
        except:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.user_login_error,
                code=RESPONSE_CODES.error,
                data={})

    #####################################
    # Logout User
    #####################################
    @classmethod
    async def LogoutUser(self, user_ins):
        try:
            logout_user = await AUTH_TASK.LogoutUser(user_ins)
            print(f'logout_user {logout_user}')
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
            print(f'delete_user {delete_user}')

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
    async def GenerateAndSendForgotPasswordLink(self, data):
        try:
            link = ''
            # Check if user exist
            is_user_exist = await AUTH_TASK.IsUserExist(username=data.username)
            print(f'is user exist {is_user_exist}')
            
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
                    print(f'link {link}')

                    # Send Email
                    user_profile_data= await AUTH_TASK.GetUserProfileDataByUsername(username=data.username)
                    print(f'user_profile_data {user_profile_data}')

                        # Send Email
                    if(user_profile_data):
                        is_email_sent = await AUTH_TASK.SendForgotPasswordEmail(user_profile_data=user_profile_data,link=link)
                        if(is_email_sent):                       
                            return LocalResponse(
                                response=RESPONSE_MESSAGES.success,
                                message=RESPONSE_MESSAGES.send_link_success,
                                code=RESPONSE_CODES.success,
                                data={
                                    'link':link,
                                })
                        else:
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
            print(f'data {data}')
            if(data.password != data.confirm_password):
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.password_not_match,
                    code=RESPONSE_CODES.error,
                    data={})

            # Validate Password
            validate_password = await AUTH_VALIDATOR._validate_password(password=data.password)
            print(f'validate_password {validate_password}')

            if validate_password.code == RESPONSE_CODES.error:
                return LocalResponse(
                    code=RESPONSE_CODES.error,
                    response=RESPONSE_MESSAGES.error,
                    message=validate_password.message,
                    data={})
        
            # Decode the hash and get time difference
            time_difference =  await AUTH_TASK.DecodeHashAndGetTimeDifference(hash=data.hash)
            if time_difference < STATICVALUES.PASSWORD_RESET_TIME_LIMIT:
                print(f'time_difference {time_difference}')
                
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
            print(f'Error: {e}')
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
            print(f'hash {hash}')
            time_difference =  await AUTH_TASK.DecodeHashAndGetTimeDifference(hash=hash)
            if time_difference > 59:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.link_expired_error,
                    code=RESPONSE_CODES.error,
                    data={
                        'time_difference':time_difference,
                    })
            data = {
                'key':hash,
                'expire_in': (STATICVALUES.PASSWORD_RESET_TIME_LIMIT-time_difference),

            }
            
            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.default_success,
                code=RESPONSE_CODES.success,
                data=data)

        except Exception as e:
            print(f'Error: {e}')
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.default_error,
                code=RESPONSE_CODES.error,
                data={})

    #####################################
    # Reset Password
    #####################################
    @classmethod
    async def ResetPassword(self, user_ins, data):
        try:
            # Validate Password
            validate_password = await AUTH_VALIDATOR._validate_password(password=data.password)
            print(f'validate_password')

            if validate_password.code == RESPONSE_CODES.error:
                return LocalResponse(
                    code=RESPONSE_CODES.error,
                    response=RESPONSE_MESSAGES.error,
                    message=validate_password.message,
                    data={})
            
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