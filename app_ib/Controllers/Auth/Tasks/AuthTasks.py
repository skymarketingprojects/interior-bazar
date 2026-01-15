import base64
import hashlib
import json
from interior_bazzar  import settings
from app_ib.serializers import MyTokenObtainPairSerializer
from django.contrib.auth.hashers import make_password, check_password
from app_ib.models import CustomUser, UserProfile
from app_ib.Utils.AppMode import APPMODE, APPMODE_URL
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.Utils.Names import NAMES
from asgiref.sync import sync_to_async

class AUTH_TASK:

    @classmethod
    async def IsUserExist(self, username):
        try:
            """Check if user exists in database"""
            is_user_exist = await sync_to_async(CustomUser.objects.filter(username=username).exists)()
            return is_user_exist
        except Exception as e:
            await MY_METHODS.printStatus(f'Error in IsUserExist {e}')
            return None

    @classmethod
    async def IsUserExistByMail(self, email):
        try:
            """Check if user exists in database"""
            is_user_exist = await sync_to_async(CustomUser.objects.filter(email=email).exists)()
            return is_user_exist
        except Exception as e:
            # await MY_METHODS.printStatus(f'Error in IsUserExist {e}')
            return None
        
    @classmethod
    async def CreateUser(self, username, password, type):
        try:
            """Create user in database"""
            user_ins = CustomUser()
            user_ins.username= username
            user_ins.password = make_password(password)
            user_ins.type= type
            user_ins.is_active= True
            user_ins.is_delete= False
            await sync_to_async(user_ins.save)()
            return user_ins
        except Exception as e:
            # await MY_METHODS.printStatus(f'Error in CreateUser {e}')
            return None

    @classmethod
    async def GenerateUserToken(self, user_ins):
        try:
            """Generate user token"""
            token = await MyTokenObtainPairSerializer.get_token(user=user_ins)
            access_token = token[NAMES.ACCESS]
            refresh_token = token[NAMES.REFRESH]
            data = {
                NAMES.ACCESS_TOKEN:access_token,
                NAMES.REFRESH_TOKEN:refresh_token,
                NAMES.TYPE:user_ins.type,
                NAMES.USERID:user_ins.id,
                NAMES.USERNAME:user_ins.username,
                NAMES.ISACTIVE:user_ins.is_active,
                NAMES.IS_DELETE:user_ins.is_delete,
                NAMES.UNIQUE_ID:user_ins.unique_id
            }
            return data
        except Exception as e:
            # await MY_METHODS.printStatus(f'Error in GenerateUserToken {e}')
            return None

    @classmethod
    async def LoginUser(self, username, password):
        try:
            """Check if user exists in database"""
            user = await sync_to_async(CustomUser.objects.get)(username=username)
            if check_password(password, user.password):
                return user
            return False
        except Exception as e:
            # await MY_METHODS.printStatus(f'Error in IsUserExist {e}')
            return False

    @classmethod
    async def LogoutUser(self,user_ins):
        try:
            return True
        except Exception as e:
            # await MY_METHODS.printStatus(f'Error in IsUserExist {e}')
            return None

    @classmethod
    async def DeleteUser(self,user_ins):
        try:
            user_ins.is_delete= True
            await sync_to_async(user_ins.save)()
            return True
        except Exception as e:
            return None


    #####################################
    # Generate Forgot Password Link
    #####################################
    @classmethod
    async def GenerateForgotPasswordLink(self,username, timestamp):
        try:
            json_of_hash = {
                NAMES.USERNAME:username,
                NAMES.TIMESTAMP:timestamp
            }
            json_of_hash = json.dumps(json_of_hash)
            encoded_hash = base64.urlsafe_b64encode(json_of_hash.encode()).decode()
            
            if(settings.ENV==APPMODE.LOC):
                link = f'{APPMODE_URL.LOC}v-1/forgot-password/{encoded_hash}'

            if(settings.ENV==APPMODE.DEV):
                link = f'{APPMODE_URL.DEV}v-1/forgot-password/{encoded_hash}'

            else:
                link = f'{APPMODE_URL.PROD}v-1/forgot-password/{encoded_hash}'
            return link
        except Exception as e:
            # await MY_METHODS.printStatus(f'Error in GenerateForgotPasswordLink {e}')
            return None

    #####################################
    # Get User Profile Data By Username
    #####################################
    @classmethod
    async def GetUserProfileDataByUsername(self,username):
        try:
            is_user_exist = await sync_to_async(CustomUser.objects.filter(username=username).exists)()

            if is_user_exist:
                user_ins = await sync_to_async(CustomUser.objects.get)(username=username)
                user_profile_ins = await sync_to_async(UserProfile.objects.filter(user=user_ins).first)()
                data = {
                    NAMES.EMAIL:user_profile_ins.email,
                    NAMES.PHONE:user_profile_ins.phone,
                    NAMES.NAME:user_profile_ins.name,
                }
                return data 
                           
            else:
                return False
        except Exception as e:
            # await MY_METHODS.printStatus(f'Getting UserProfile instance error {e}')
            return None

    #####################################
    # Send Forgot Password Email
    #####################################
    @classmethod
    async def SendForgotPasswordEmail(self,user_profile_data,link):
        try:
            email = user_profile_data[NAMES.EMAIL]
            await MY_METHODS.send_email(
                email=email,
                subject='Forgot Password',
                message=f'Click on the link to reset password {link}'
            )
            return True
        except Exception as e:
            # await MY_METHODS.printStatus(f'Error in SendForgotPasswordEmail {e}')
            return None
    
    ###############################################
    # Reset Password
    ###############################################
    @classmethod
    async def ResetPassword(self, user_ins, data):
        try:
            if(user_ins.password==data.old_password):
                user_ins.password = make_password(data.password)
                await sync_to_async(user_ins.save)()
                return True
            else:
                return False

        except Exception as e:
            # await MY_METHODS.printStatus(f'Error in ResetPassword {e}')
            return None



    @classmethod
    async def DecodeHashAndGetTimeDifference(self,hash):
        try:
            decoded_json_str = base64.urlsafe_b64decode(hash.encode()).decode()
            decode_hash = json.loads(decoded_json_str)
            username = decode_hash[NAMES.USERNAME]
            timestamp = decode_hash[NAMES.TIMESTAMP]
            time_difference =  await MY_METHODS.GetTimeDifferenceInMinutes(my_time=timestamp)
            return time_difference
        except Exception as e:
            # await MY_METHODS.printStatus(f'Error in DecodeHash {e}')
            return None

    ###############################################
    # Change Password
    ###############################################
    @classmethod
    async def ChangePassword(self, hash, password):
        try:
            # await MY_METHODS.printStatus(f'hash {hash}')
            # await MY_METHODS.printStatus(f'password {password}')

            decoded_json_str = base64.urlsafe_b64decode(hash.encode()).decode()
            decode_hash = json.loads(decoded_json_str)
            username = decode_hash[NAMES.USERNAME]
            # await MY_METHODS.printStatus(f'username {username}')
            

            user_ins = await sync_to_async(CustomUser.objects.get)(username=username)
            user_ins.password = make_password(password)
            await sync_to_async(user_ins.save)()
            return True

        except Exception as e:
            # await MY_METHODS.printStatus(f'Error in ResetPassword {e}')
            return None