from asgiref.sync import sync_to_async
from adrf.decorators import api_view
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.Utils.LocalResponse import LocalResponse
from interior_business.Controllers.Business.Tasks.BusinessTasks import BUSS_TASK
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.models import BusinessProfile, Business
from interior_business.Controllers.BusinessProfile.Tasks.BusinessProfileTasks import BUSS_PROF_TASK


class BUSS_PROFILE_CONTROLLER:

    @classmethod
    async def GetBusinessProfileForDisplay(self, business_id):
        try:
            get_resp = await BUSS_PROF_TASK.GetBusinessProfileTask(business_id=business_id)
            if 'error' not in get_resp:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.success,
                    message=RESPONSE_MESSAGES.business_prof_fetch_success,
                    code=RESPONSE_CODES.success,
                    data=get_resp)
            else:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.business_prof_fetch_error,
                    code=RESPONSE_CODES.error,
                    data={})
        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.business_prof_fetch_error,
                code=RESPONSE_CODES.error,
                data={
                    'error': str(e)
                })
  
    @classmethod
    async def CreateOrUpdateBusinessProfile(self, user_ins, data):
        try:
            business_ins = None
            business_loc_ins= None

            is_business_exist = await sync_to_async(Business.objects.filter(user=user_ins).exists)()
            #await MY_METHODS.printStatus(f'is_business_exist {is_business_exist}')

            if(is_business_exist):
                 business_ins = await sync_to_async(Business.objects.get)(user=user_ins)

            # Check if business already exist
            is_business_prof_exist = await sync_to_async(BusinessProfile.objects.filter(business=business_ins).exists)()
            #await MY_METHODS.printStatus(f'is_business_prof_exist {is_business_prof_exist}')

            if is_business_prof_exist:
                business_prof_ins = await sync_to_async(BusinessProfile.objects.get)(business=business_ins)
                #await MY_METHODS.printStatus(f'update business profile')
                update_resp = await BUSS_PROF_TASK.UpdateBusinessProfileTask(business_prof_ins=business_prof_ins,data=data)

                if update_resp:
                    return LocalResponse(
                        response=RESPONSE_MESSAGES.success,
                        message=RESPONSE_MESSAGES.business_prof_update_success,
                        code=RESPONSE_CODES.success,
                        data={})
                else:
                    return LocalResponse(
                        response=RESPONSE_MESSAGES.error,
                        message=RESPONSE_MESSAGES.business_prof_update_error,
                        code=RESPONSE_CODES.error,
                        data={})

            else:
                #await MY_METHODS.printStatus(f'create business location')
                create_resp = await BUSS_PROF_TASK.CreateBusinessProfileTask(
                    business_ins=business_ins, data=data)
                if create_resp:
                    return LocalResponse(
                        response=RESPONSE_MESSAGES.success,
                        message=RESPONSE_MESSAGES.business_prof_create_success,
                        code=RESPONSE_CODES.success,
                        data={})
                else:
                    return LocalResponse(
                        response=RESPONSE_MESSAGES.error,
                        message=RESPONSE_MESSAGES.business_prof_create_error,
                        code=RESPONSE_CODES.error,
                        data={})
        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.business_prof_create_error,
                code=RESPONSE_CODES.error,
                data={
                    'error': str(e)
                })

    @classmethod
    async def GetBuisnessProfByBusinessID(self,id):
        try:
            business_ins = None
            business_prof_ins= None

            is_business_exist = await sync_to_async(Business.objects.filter(pk=id).exists)()
            #await MY_METHODS.printStatus(f'is_business_exist {is_business_exist}')

            if(is_business_exist):
                 business_ins = await sync_to_async(Business.objects.get)(pk=id)

            # Check if business already exist
            is_business_loc_exist = await sync_to_async(BusinessProfile.objects.filter(business=business_ins).exists)()

            if is_business_loc_exist:
                business_prof_ins = await sync_to_async(BusinessProfile.objects.get)(business=business_ins)

                update_resp = await BUSS_PROF_TASK.GetBusinessProfTask(
                    business_prof_ins=business_prof_ins)
                if update_resp:
                    return LocalResponse(
                        response=RESPONSE_MESSAGES.success,
                        message=RESPONSE_MESSAGES.business_prof_fetch_success,
                        code=RESPONSE_CODES.success,
                        data=update_resp)

                else:
                    return LocalResponse(
                        response=RESPONSE_MESSAGES.error,
                        message=RESPONSE_MESSAGES.business_prof_fetch_error,
                        code=RESPONSE_CODES.error,
                        data={})

        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.business_prof_fetch_error,
                code=RESPONSE_CODES.error,
                data={
                    'error': str(e)
                })

    @classmethod 
    async def CreateOrUpdatePrimaryImage(self, user_ins, primary_image):
        try:
            business_ins = None
            is_business_exist = await sync_to_async(Business.objects.filter(user=user_ins).exists)()
            #await MY_METHODS.printStatus(f'is_business_exist {is_business_exist}')

            if(is_business_exist): 
                business_ins = await sync_to_async(Business.objects.get)(user=user_ins)

            is_buss_prof_ins_exist = await sync_to_async(BusinessProfile.objects.filter(business=business_ins).exists)()
            #await MY_METHODS.printStatus(f'is_buss_prof_ins_exist {is_buss_prof_ins_exist}')

            # Update Profile Image if already exist : 
            if is_buss_prof_ins_exist:
                profile_ins = await sync_to_async(BusinessProfile.objects.get)(business=business_ins)
                profile_ins.primary_image = primary_image
                await sync_to_async(profile_ins.save)()

            # Create Profile Image if not exist : 
            else:
                profile_ins = BusinessProfile()
                profile_ins.business = business_ins
                profile_ins.primary_image = primary_image
                await sync_to_async(profile_ins.save)()
            
            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.update_success,
                code=RESPONSE_CODES.success,
                data={})

        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.default_error,
                code=RESPONSE_CODES.error,
                data={
                    'error': str(e)
                })

    @classmethod 
    async def CreateOrUpdateSecondaryImage(self, user_ins, secondary_image):
        try:
            business_ins = None
            is_business_exist = await sync_to_async(Business.objects.filter(user=user_ins).exists)()
            #await MY_METHODS.printStatus(f'is_business_exist {is_business_exist}')

            if(is_business_exist): 
                business_ins = await sync_to_async(Business.objects.get)(user=user_ins)

            is_buss_prof_ins_exist = await sync_to_async(BusinessProfile.objects.filter(business=business_ins).exists)()
            #await MY_METHODS.printStatus(f'is_buss_prof_ins_exist {is_buss_prof_ins_exist}')

            # Update Profile Image if already exist : 
            if is_buss_prof_ins_exist:
                profile_ins = await sync_to_async(BusinessProfile.objects.get)(business=business_ins)
                profile_ins.secondary_images = secondary_image
                await sync_to_async(profile_ins.save)()

            # Create Profile Image if not exist : 
            else:
                profile_ins = BusinessProfile()
                profile_ins.business = business_ins
                profile_ins.secondary_images = secondary_image
                await sync_to_async(profile_ins.save)()
            
            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.update_success,
                code=RESPONSE_CODES.success,
                data={})

        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.default_error,
                code=RESPONSE_CODES.error,
                data={
                    'error': str(e)
                })
        