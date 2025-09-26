from asgiref.sync import sync_to_async
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.models import LeadQuery
from app_ib.Controllers.AdsQuery.Tasks.AdsQueryTasks import ADS_QUERY_TASKS
from app_ib.Utils.MyMethods import MY_METHODS

class ADS_QUERY_CONTROLLER:
    @classmethod
    async def CreateAdsQuery(self,data):
        try:
            create_query_resp = await  ADS_QUERY_TASKS.CreateAdsQueryTask(data=data)
            #await MY_METHODS.printStatus(f'create query resp {create_query_resp}')

            if create_query_resp:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.success,
                    message=RESPONSE_MESSAGES.ads_query_generate_success,
                    code=RESPONSE_CODES.success,
                    data=create_query_resp)

            else:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.ads_query_generate_error,
                    code=RESPONSE_CODES.error,
                    data={})

        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.ads_query_generate_error,
                code=RESPONSE_CODES.error,
                data={
                    'error': str(e)
                })


    @classmethod
    async def VerifyAdsQuery(self, data):
        try:

            is_query_exist = await sync_to_async(LeadQuery.objects.filter(id=data.id).exists)()
            #await MY_METHODS.printStatus(f'is_query_exist {is_query_exist}')

            if(is_query_exist):
                lead_query_ins = await sync_to_async(LeadQuery.objects.get)(id=data.id)
                #await MY_METHODS.printStatus(f'lead_query_ins {lead_query_ins}')   
                
                create_query_resp = await  ADS_QUERY_TASKS.VerifyAdsQueryTask(lead_query_ins=lead_query_ins,data=data)
                #await MY_METHODS.printStatus(f'verify query resp {create_query_resp}')

                if create_query_resp:
                    return LocalResponse(
                        response=RESPONSE_MESSAGES.success,
                        message=RESPONSE_MESSAGES.ads_query_update_success,
                        code=RESPONSE_CODES.success,
                        data=create_query_resp)

                else:
                    return LocalResponse(
                        response=RESPONSE_MESSAGES.error,
                        message=RESPONSE_MESSAGES.ads_query_update_success,
                        code=RESPONSE_CODES.error,
                        data={})

        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.ads_query_update_error,
                code=RESPONSE_CODES.error,
                data={
                    'error': str(e)
                })