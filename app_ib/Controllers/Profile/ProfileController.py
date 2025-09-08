from asgiref.sync import sync_to_async
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.models import UserProfile
from app_ib.Controllers.Profile.Tasks.Taskys import PROFILE_TASKS

class PROFILE_CONTROLLER:
###########################################
 # Create or update Profile
 ########################################### 
    @classmethod 
    async def CreateOrUpdateProfile(self, user_ins , data):
        try:
            # Test
            # print(f'user instance {user_ins}')
            # print(f'name {data.name}')
            # print(f'email {data.email}')
            # print(f'phone {data.phone}')

            is_user_profile_created = await sync_to_async(UserProfile.objects.filter(user=user_ins).exists)()
            print(f'is user profile created {is_user_profile_created}')
            
            if(is_user_profile_created):
                user_profile_ins = await sync_to_async(UserProfile.objects.get)(user=user_ins)
                is_profile_updated= await PROFILE_TASKS.UpdateProfileTask(user_profile_ins=user_profile_ins,data=data)
                print(f'is profile created {is_profile_updated}')

                if(is_profile_updated):
                    profile_data = await PROFILE_TASKS.GetProfileDataTask(user_profile_ins=user_profile_ins)
                    return LocalResponse(
                        response=RESPONSE_MESSAGES.success,
                        message=RESPONSE_MESSAGES.user_profile_update_success,
                        code=RESPONSE_CODES.success,
                        data=profile_data)
                else:
                    return LocalResponse(
                        response=RESPONSE_MESSAGES.error,
                        message=RESPONSE_MESSAGES.user_profile_update_error,
                        code=RESPONSE_CODES.error,
                        data={})
                    
            else:
                is_profile_created= await PROFILE_TASKS.CreateProfileTask(user_ins=user_ins,data=data)
                print(f' is profile updated {is_profile_created}')
                
                if(is_profile_created):
                    return LocalResponse(
                        response=RESPONSE_MESSAGES.success,
                        message=RESPONSE_MESSAGES.user_profile_create_success,
                        code=RESPONSE_CODES.success,
                        data={})
                else:
                    return LocalResponse(
                        response=RESPONSE_MESSAGES.error,
                        message=RESPONSE_MESSAGES.user_profile_create_error,
                        code=RESPONSE_CODES.error,
                        data={})
                
        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.user_profile_create_error,
                code=RESPONSE_CODES.error,
                data={
                    'error': str(e)
                })
            
 ###########################################
 # Create or update profile image   
 ########################################### 
    @classmethod 
    async def CreateOrUpdateProfileImage(self, user_ins , profile_image):
        try:
            # Test
            # print(f'user instance {user_ins}')
            # print(f'profile image {profile_image}')
            
            is_user_profile_created = await sync_to_async(UserProfile.objects.filter(user=user_ins).exists)()
            print(f'is user profile created {is_user_profile_created}')

            # Update Profile Image if already exist : 
            if is_user_profile_created:
                user_profile_ins = await sync_to_async(UserProfile.objects.get)(user=user_ins)
                is_profile_image_updated = await PROFILE_TASKS.UpdateProfileImageTask(user_profile_ins=user_profile_ins,profile_image=profile_image)

                if(is_profile_image_updated):
                    return LocalResponse(
                        response=RESPONSE_MESSAGES.success,
                        message=RESPONSE_MESSAGES.user_profile_update_success,
                        code=RESPONSE_CODES.success,
                        data={})
                else:
                    return LocalResponse(
                        response=RESPONSE_MESSAGES.error,
                        message=RESPONSE_MESSAGES.user_profile_update_error,
                        code=RESPONSE_CODES.error,
                        data={
                            'msg':"update task error"
                        })
            # Create Profile Image if not exist : 
            else:
                is_profile_image_created= await PROFILE_TASKS.CreateProfileImageTask(user_ins=user_ins,profile_image=profile_image)
                print(f' is profile image created {is_profile_image_created}')

                if(is_profile_image_created):
                    return LocalResponse(
                        response=RESPONSE_MESSAGES.success,
                        message=RESPONSE_MESSAGES.user_profile_update_success,
                        code=RESPONSE_CODES.success,
                        data={})
                else:
                    return LocalResponse(
                        response=RESPONSE_MESSAGES.error,
                        message=RESPONSE_MESSAGES.user_profile_update_error,
                        code=RESPONSE_CODES.error,
                        data={
                            'msg':"create task error"
                        })

        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.user_profile_update_error,
                code=RESPONSE_CODES.error,
                data={
                    'error': str(e)
                })


 ###########################################
 # GetProfile   
 ###########################################                   
    @classmethod 
    async def GetProfile(self, user_ins):
        try:
            print(f'user instance {user_ins}')
            
            is_user_profile_created = await sync_to_async(UserProfile.objects.filter(user=user_ins).exists)()
            print(f'is user profile created {is_user_profile_created}')
            
            # Update Profile Image if already exist : 
            if is_user_profile_created:
                user_profile_ins = await sync_to_async(UserProfile.objects.get)(user=user_ins)
                user_profile_data= await PROFILE_TASKS.GetProfileDataTask(user_profile_ins=user_profile_ins)
                user_profile_data["username"] = user_ins.username
                user_profile_data["role"] = user_ins.type
                user_profile_data["id"] = user_ins.id
                
                return LocalResponse(
                    response=RESPONSE_MESSAGES.success,
                    message=RESPONSE_MESSAGES.user_profile_fetch_success,
                    code=RESPONSE_CODES.success,
                    data=user_profile_data)
            

        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.user_profile_fetch_error,
                code=RESPONSE_CODES.error,
                data={
                    'error': str(e)
                })
