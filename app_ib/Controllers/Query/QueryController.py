from asgiref.sync import sync_to_async
from adrf.decorators import api_view
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.Names import NAMES
from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.models import LeadQuery, Business,CustomUser
from app_ib.Controllers.Query.Tasks.QueryTasks import LEAD_QUERY_TASK
from .Validators.QueryValidators import leadQuerysData,leadData
from django.db.models import Q

class LEAD_QUERY_CONTROLLER:

    @classmethod
    async def GetQueries(self,user_ins):
        try:
            lead_query_ins= None
            lead_query_ins = await sync_to_async(
                lambda: LeadQuery.objects.filter(user=user_ins).all().order_by(f'-{NAMES.TIMESTAMP}')
            )()
            (f'lead_query_ins {lead_query_ins}')   
            leads_data = []

            for leads in lead_query_ins:
                data = await LEAD_QUERY_TASK.GetLeadQueryTask(leads)
                leads_data.append(data)

            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.query_fetch_success,
                code=RESPONSE_CODES.success,
                data=leads_data)

        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.query_fetch_error,
                code=RESPONSE_CODES.error,
                data={
                    NAMES.ERROR: str(e)
                })
    @classmethod
    async def CreateLeadQuery(self,data,user:CustomUser=None):
        try:

            create_query_resp,data = await  LEAD_QUERY_TASK.CreateLeadQueryTask(data=data,user=user)
            await MY_METHODS.printStatus(f'create query resp {create_query_resp}')

            if create_query_resp:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.success,
                    message=RESPONSE_MESSAGES.query_generate_success,
                    code=RESPONSE_CODES.success,
                    data=data)

            else:
                return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.query_generate_error,
                code=RESPONSE_CODES.error,
                data=data)

        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.query_generate_error,
                code=RESPONSE_CODES.error,
                data={
                    NAMES.ERROR: str(e)
                })

    @classmethod
    async def UpdateLeadQuery(self, data:leadData):
        try:
            lead_query_ins= None
            is_query_exist = await sync_to_async(LeadQuery.objects.filter(id=data.id).exists)()
            await MY_METHODS.printStatus(f'is_query_exist {is_query_exist}')

            if(is_query_exist):
                lead_query_ins = await sync_to_async(LeadQuery.objects.get)(id=data.id)
                await MY_METHODS.printStatus(f'lead_query_ins {lead_query_ins}')
                
                create_query_resp = await  LEAD_QUERY_TASK.UpdateLeadQueryTask(lead_query_ins=lead_query_ins,data=data)
                # await MY_METHODS.printStatus(f'update query resp {create_query_resp}')
                
                if create_query_resp:
                    return LocalResponse(
                        response=RESPONSE_MESSAGES.success,
                        message=RESPONSE_MESSAGES.query_update_success,
                        code=RESPONSE_CODES.success,
                        data=create_query_resp)

                else:
                    return LocalResponse(
                        response=RESPONSE_MESSAGES.error,
                        message=RESPONSE_MESSAGES.query_update_error,
                        code=RESPONSE_CODES.error,
                        data={}
                        )

        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.query_update_error,
                code=RESPONSE_CODES.error,
                data={
                    NAMES.ERROR: str(e)
                })

    @classmethod
    async def UpdateLeadQueryStatus(self, data,user:CustomUser=None):
        try:
            lead_query_ins= None
            is_query_exist = await sync_to_async(LeadQuery.objects.filter(id=data.id).exists)()
            (f'is_query_exist {is_query_exist}')

            if(is_query_exist):
                lead_query_ins = await sync_to_async(LeadQuery.objects.get)(id=data.id)
                (f'lead_query_ins {lead_query_ins}')   
                
                create_query_resp = await  LEAD_QUERY_TASK.UpdateLeadQueryStatusTask(lead_query_ins=lead_query_ins,data=data)
                (f'update query resp {create_query_resp}')

                if create_query_resp:
                    return LocalResponse(
                        response=RESPONSE_MESSAGES.success,
                        message=RESPONSE_MESSAGES.query_update_success,
                        code=RESPONSE_CODES.success,
                        data=create_query_resp)

                else:
                    return LocalResponse(
                        response=RESPONSE_MESSAGES.error,
                        message=RESPONSE_MESSAGES.query_update_error,
                        code=RESPONSE_CODES.error,
                        data={})

        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.query_update_error,
                code=RESPONSE_CODES.error,
                data={
                    NAMES.ERROR: str(e)
                })

    @classmethod
    async def UpdateLeadQueryPriority(self, data):
        try:
            lead_query_ins= None
            is_query_exist = await sync_to_async(LeadQuery.objects.filter(id=data.id).exists)()
            (f'is_query_exist {is_query_exist}')

            if(is_query_exist):
                lead_query_ins = await sync_to_async(LeadQuery.objects.get)(id=data.id)
                (f'lead_query_ins {lead_query_ins}')   
                
                create_query_resp = await  LEAD_QUERY_TASK.UpdateLeadQueryPriorityTask(lead_query_ins=lead_query_ins,data=data)
                (f'update query resp {create_query_resp}')

                if create_query_resp:
                    return LocalResponse(
                        response=RESPONSE_MESSAGES.success,
                        message=RESPONSE_MESSAGES.query_update_success,
                        code=RESPONSE_CODES.success,
                        data=create_query_resp)

                else:
                    return LocalResponse(
                        response=RESPONSE_MESSAGES.error,
                        message=RESPONSE_MESSAGES.query_update_error,
                        code=RESPONSE_CODES.error,
                        data={})

        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.query_update_error,
                code=RESPONSE_CODES.error,
                data={
                    NAMES.ERROR: str(e)
                })

    @classmethod
    async def UpdateLeadQueryRemark(self, data):
        try:
            lead_query_ins= None
            is_query_exist = await sync_to_async(LeadQuery.objects.filter(id=data.id).exists)()
            (f'is_query_exist {is_query_exist}')

            if(is_query_exist):
                lead_query_ins = await sync_to_async(LeadQuery.objects.get)(id=data.id)
                (f'lead_query_ins {lead_query_ins}')   
                
                create_query_resp = await  LEAD_QUERY_TASK.UpdateLeadQueryRemarkTask(lead_query_ins=lead_query_ins,data=data)
                (f'update query resp {create_query_resp}')

                if create_query_resp:
                    return LocalResponse(
                        response=RESPONSE_MESSAGES.success,
                        message=RESPONSE_MESSAGES.query_update_success,
                        code=RESPONSE_CODES.success,
                        data=create_query_resp)

                else:
                    return LocalResponse(
                        response=RESPONSE_MESSAGES.error,
                        message=RESPONSE_MESSAGES.query_update_error,
                        code=RESPONSE_CODES.error,
                        data={})

        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.query_update_error,
                code=RESPONSE_CODES.error,
                data={
                    NAMES.ERROR: str(e)
                })

    @classmethod
    async def GetQueryById(self, id):
        try:
            lead_query_ins= None
            is_query_exist = await sync_to_async(LeadQuery.objects.filter(id=id).exists)()
            (f'is_query_exist {is_query_exist}')

            if(is_query_exist):
                lead_query_ins = await sync_to_async(LeadQuery.objects.get)(id=id)
                (f'lead_query_ins {lead_query_ins}') 
                
                fetch_query_response = await  LEAD_QUERY_TASK.GetLeadQueryTask(lead_query_ins=lead_query_ins)
                (f'update query resp {fetch_query_response}')

                if fetch_query_response:
                    return LocalResponse(
                        response=RESPONSE_MESSAGES.success,
                        message=RESPONSE_MESSAGES.query_fetch_success,
                        code=RESPONSE_CODES.success,
                        data=fetch_query_response)

                else:
                    return LocalResponse(
                        response=RESPONSE_MESSAGES.error,
                        message=RESPONSE_MESSAGES.query_fetch_error,
                        code=RESPONSE_CODES.error,
                        data={})

        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.query_fetch_error,
                code=RESPONSE_CODES.error,
                data={
                    NAMES.ERROR: str(e)
                })

    @classmethod
    async def GetBusinessQueries(self, user_ins,queryParams:leadQuerysData):
        try:
            lead_query_ins= None

            is_business_exist = await sync_to_async(Business.objects.filter(user=user_ins).exists)()
            (f'is_business_exist {is_business_exist}')

            if(is_business_exist):
                business_ins = await sync_to_async(Business.objects.get)(user=user_ins)
                params=Q(business=business_ins)


                if queryParams.status:
                    params &=  Q(status=queryParams.status)

                if queryParams.priority:
                    params &= Q(priority=queryParams.priority)

                if queryParams.fromDate and queryParams.toDate:
                    params &=Q(timestamp__range=[queryParams.fromDate, queryParams.toDate])

                if queryParams.leadFor:
                    if queryParams.leadFor == NAMES.PRODUCT:
                        params &= Q(product__isnull=False)
                    elif queryParams.leadFor == NAMES.SERVICE:
                        params &= Q(service__isnull=False)
                    elif queryParams.leadFor == NAMES.CATALOUGE:
                        params &= Q(catalouge__isnull=False)
                
                buss_queries = await LEAD_QUERY_TASK.GetLeadQueriesTask(queryParams=params)
                #  (f'queries {buss_queries}')
                if buss_queries:
                    return LocalResponse(
                        response=RESPONSE_MESSAGES.success,
                        message=RESPONSE_MESSAGES.query_fetch_success,
                        code=RESPONSE_CODES.success,
                        data=buss_queries)

                else:
                    return LocalResponse(
                        response=RESPONSE_MESSAGES.error,
                        message=RESPONSE_MESSAGES.query_fetch_error,
                        code=RESPONSE_CODES.error,
                        data={})

        except Exception as e:
            (f'fetch quries error {e}')
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.query_fetch_error,
                code=RESPONSE_CODES.error,
                data={
                    NAMES.ERROR: str(e)
                })



        
