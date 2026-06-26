from asgiref.sync import sync_to_async
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.Names import NAMES
from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.models import UserProfile,CustomUser
from app_ib.Controllers.Profile.Tasks.Taskys import PROFILE_TASKS
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.Controllers.Plans.PlanController import PLAN_CONTROLLER
from interior_notification.signals import userSignupSignal
import asyncio
from app_ib.Controllers.Profile.Validators.ProfileValidators import (
    ProfileCreateOrUpdateSchema
)

class PROFILE_CONTROLLER:
###########################################
 # Create or update Profile
 ########################################### 
    @classmethod 
    async def CreateOrUpdateProfile(self, user_ins , data:ProfileCreateOrUpdateSchema):
        try:

            is_user_profile_created = await sync_to_async(UserProfile.objects.filter(user=user_ins).exists)()
            
            if(is_user_profile_created):
                user_profile_ins = await sync_to_async(UserProfile.objects.get)(user=user_ins)
                is_profile_updated= await PROFILE_TASKS.UpdateProfileTask(user_profile_ins=user_profile_ins,data=data)

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
    async def CreateOrUpdateProfileImage(self, user_ins:CustomUser , profile_image):
        try:
            
            is_user_profile_created = await sync_to_async(UserProfile.objects.filter(user=user_ins).exists)()

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
    async def GetProfileData(cls, userIns:CustomUser, includePlan=False):
        try:
            is_user_profile_created = await sync_to_async(UserProfile.objects.filter(user=userIns).exists)()
            
            user_data = {
                NAMES.USERNAME: userIns.username,
                NAMES.ROLE: userIns.type,
                NAMES.ID: userIns.id,
                'isSuperAdmin': False
            }

            # Expose the owned business id so the seller dashboard can load the
            # business profile (it resolves the entity from user.businessId).
            # A soft-deleted business (isActive=False) is treated as none so the
            # dashboard falls back to the create flow instead of loading a hidden row.
            def _resolve_business_id():
                biz = getattr(userIns, NAMES.USER_BUSINESS_RELATION, None)
                if biz is None or not getattr(biz, 'isActive', True):
                    return None
                return getattr(biz, NAMES.ID, None)
            business_id = await sync_to_async(_resolve_business_id)()
            if business_id is not None:
                user_data[NAMES.BUSINESS_ID] = business_id

            if userIns.type == NAMES.ADMIN:
                user_data['isSuperAdmin'] = await sync_to_async(userIns.roles.filter(is_full_access=True).exists)()

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
    async def GetProfile(cls, userIns: CustomUser):
        # Always try to include plan if user has a business or is marked as business type
        # This ensures planId is available immediately after login (fixing the "refresh to see plan" bug)
        try:
            has_business = await sync_to_async(lambda: hasattr(userIns, 'user_business'))()
            if has_business or userIns.type == NAMES.BUSINESS:
                return await cls.GetProfileData(userIns, includePlan=True)
        except:
            pass
        return await cls.GetProfileData(userIns, includePlan=False)

    @classmethod
    async def GetProfileDashbord(cls, userIns):
        return await cls.GetProfileData(userIns, includePlan=True)
