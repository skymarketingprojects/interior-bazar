from asgiref.sync import sync_to_async
from adrf.decorators import api_view
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.Controllers.Business.Tasks.BusinessTasks import BUSS_TASK
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.models import Location
from app_ib.Controllers.ClientLocation.Tasks.ClientLocationTasks import CLIENT_LOC_TASKS


class CLIENT_LOCATION_CONTROLLER:
  
    @classmethod
    async def CreateOrUpdateClientLocation(self, user_ins, data):
        try:
            is_client_loc_exist = await sync_to_async(Location.objects.filter(user=user_ins).exists)()
            if is_client_loc_exist:
                client_loc_ins = await sync_to_async(Location.objects.get)(user=user_ins)
                print(f'update location')

                update_resp = await CLIENT_LOC_TASKS.UpdateClientLocTask(
                    client_loc_ins=client_loc_ins, data=data)

                if update_resp:
                    return LocalResponse(
                        response=RESPONSE_MESSAGES.success,
                        message=RESPONSE_MESSAGES.User_loc_update_success,
                        code=RESPONSE_CODES.success,
                        data={})
                else:
                    return LocalResponse(
                        response=RESPONSE_MESSAGES.error,
                        message=RESPONSE_MESSAGES.User_loc_update_error,
                        code=RESPONSE_CODES.error,
                        data={})

            else:
                print(f'create client location')
                create_resp = await CLIENT_LOC_TASKS.CreateClientLocTask(
                    user_ins=user_ins, data=data)

                if create_resp:
                    return LocalResponse(
                        response=RESPONSE_MESSAGES.success,
                        message=RESPONSE_MESSAGES.User_loc_create_success,
                        code=RESPONSE_CODES.success,
                        data={})
                else:
                    return LocalResponse(
                        response=RESPONSE_MESSAGES.error,
                        message=RESPONSE_MESSAGES.User_loc_create_error,
                        code=RESPONSE_CODES.error,
                        data={})

        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.User_loc_create_error,
                code=RESPONSE_CODES.error,
                data={
                    'error': str(e)
                })


    @classmethod
    async def GetClientLocByUserIns(self,id):
        try:

            is_client_loc_exist = await sync_to_async(Location.objects.filter(pk=id).exists)()

            if is_client_loc_exist:
                client_loc_ins = await sync_to_async(Location.objects.get)(pk=id)

                update_resp = await CLIENT_LOC_TASKS.GetClientLocTask(
                    client_loc_ins=client_loc_ins)

                if update_resp:
                    return LocalResponse(
                        response=RESPONSE_MESSAGES.success,
                        message=RESPONSE_MESSAGES.User_loc_fetch_success,
                        code=RESPONSE_CODES.success,
                        data=update_resp)

                else:
                    return LocalResponse(
                        response=RESPONSE_MESSAGES.error,
                        message=RESPONSE_MESSAGES.User_loc_fetch_error,
                        code=RESPONSE_CODES.error,
                        data={})

        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.User_loc_fetch_error,
                code=RESPONSE_CODES.error,
                data={
                    'error': str(e)
                })
