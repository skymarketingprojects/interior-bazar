from asgiref.sync import sync_to_async
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.Names import NAMES
from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.models import UserProfile
from app_ib.Controllers.Profile.Tasks.Taskys import PROFILE_TASKS
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.Controllers.Plans.PlanController import PLAN_CONTROLLER
from interior_notification.signals import userSignupSignal
import asyncio

class PROFILE_CONTROLLER:
###########################################
 # Create or update Profile
 ########################################### 
    @classmethod 
    async def CreateOrUpdateProfile(self, user_ins , data):
        try:
            # Test
            # await MY_METHODS.printStatus(f'user instance {user_ins}')
            # await MY_METHODS.printStatus(f'name {data.name}')
            # await MY_METHODS.printStatus(f'email {data.email}')
            # await MY_METHODS.printStatus(f'phone {data.phone}')

            is_user_profile_created = await sync_to_async(UserProfile.objects.filter(user=user_ins).exists)()
            # await MY_METHODS.printStatus(f'is user profile created {is_user_profile_created}')
            
            if(is_user_profile_created):
                user_profile_ins = await sync_to_async(UserProfile.objects.get)(user=user_ins)
                is_profile_updated= await PROFILE_TASKS.UpdateProfileTask(user_profile_ins=user_profile_ins,data=data)
                # await MY_METHODS.printStatus(f'is profile created {is_profile_updated}')

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
                # await MY_METHODS.printStatus(f' is profile updated {is_profile_created}')
                asyncio.create_task(sync_to_async(userSignupSignal.send)(sender=user_ins.user_profile.__class__,instance=user_ins.user_profile,created=True))
                
                if(is_profile_created):
                    user_profile_ins = await sync_to_async(UserProfile.objects.get)(user=user_ins)
                    profile_data = await PROFILE_TASKS.GetProfileDataTask(user_profile_ins=user_profile_ins)
                    return LocalResponse(
                        response=RESPONSE_MESSAGES.success,
                        message=RESPONSE_MESSAGES.user_profile_create_success,
                        code=RESPONSE_CODES.success,
                        data=profile_data)
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
                    NAMES.ERROR: str(e)
                })
            
 ###########################################
 # Create or update profile image   
 ########################################### 
    @classmethod 
    async def CreateOrUpdateProfileImage(self, user_ins , profile_image):
        try:
            # Test
            # await MY_METHODS.printStatus(f'user instance {user_ins}')
            # await MY_METHODS.printStatus(f'profile image {profile_image}')
            
            is_user_profile_created = await sync_to_async(UserProfile.objects.filter(user=user_ins).exists)()
            # await MY_METHODS.printStatus(f'is user profile created {is_user_profile_created}')

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
                            NAMES.ERROR:"update task error"
                        })
            # Create Profile Image if not exist : 
            else:
                is_profile_image_created= await PROFILE_TASKS.CreateProfileImageTask(user_ins=user_ins,profile_image=profile_image)
                # await MY_METHODS.printStatus(f' is profile image created {is_profile_image_created}')

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
                            NAMES.ERROR:"create task error"
                        })

        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.user_profile_update_error,
                code=RESPONSE_CODES.error,
                data={
                    NAMES.ERROR: str(e)
                })


    ###########################################
    # GetProfile   
    ###########################################                   

    @classmethod
    async def GetProfileData(cls, userIns, includePlan=False):
        try:
            is_user_profile_created = await sync_to_async(UserProfile.objects.filter(user=userIns).exists)()
            
            user_data = {
                NAMES.USERNAME: userIns.username,
                NAMES.ROLE: userIns.type,
                NAMES.ID: userIns.id
            }

            if is_user_profile_created:
                user_profile_ins = await sync_to_async(UserProfile.objects.get)(user=userIns)
                user_profile_data = await PROFILE_TASKS.GetProfileDataTask(user_profile_ins=user_profile_ins)

                user_profile_data.update(user_data)

                if includePlan:
                    plan_data = await PLAN_CONTROLLER.GetBusinessPlan(user=userIns)
                    return LocalResponse(
                        response=RESPONSE_MESSAGES.success,
                        message=RESPONSE_MESSAGES.user_profile_fetch_success,
                        code=RESPONSE_CODES.success,
                        data={
                            NAMES.USER: user_profile_data,
                            NAMES.PLAN: plan_data.data
                        }
                    )
                else:
                    return LocalResponse(
                        response=RESPONSE_MESSAGES.success,
                        message=RESPONSE_MESSAGES.user_profile_fetch_success,
                        code=RESPONSE_CODES.success,
                        data=user_profile_data
                    )

            # If profile doesn't exist
            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.user_profile_fetch_success,
                code=RESPONSE_CODES.success,
                data=user_data
            )

        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.user_profile_fetch_error,
                code=RESPONSE_CODES.error,
                data={NAMES.ERROR: str(e)}
            )

    @classmethod
    async def GetProfile(cls, userIns):
        return await cls.GetProfileData(userIns, includePlan=False)

    @classmethod
    async def GetProfileDashbord(cls, userIns):
        return await cls.GetProfileData(userIns, includePlan=True)
