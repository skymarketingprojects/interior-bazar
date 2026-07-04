from asgiref.sync import sync_to_async
from app_ib.models import LeadQuery
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.Utils.Names import NAMES
from app_ib.models import Business,CustomUser
from interior_products.models import Product,Service,Catelogue
from ..Validators.QueryValidators import LeadQueryCreateSchema,LeadQueryUpdateSchema,LeadQueryStatusSchema
from interior_admin.Controllers.AdminLeads.Validators.AdminLeadsValidators import AdminLeadsCreateSchema,AdminLeadsUpdateSchema
from datetime import datetime

class LEAD_QUERY_TASK:

    @classmethod
    async def CreateLeadQueryTask(self, data:LeadQueryCreateSchema|AdminLeadsCreateSchema,user:CustomUser=None):
        try:
            lead_query_ins = LeadQuery()

            # using getattr to not get error when field is absent
            lead_query_ins.name= getattr(data, 'name', None) or ""
            lead_query_ins.phone= getattr(data, 'phone', None) or ""
            lead_query_ins.email= getattr(data, 'email', None) or ""
            lead_query_ins.interested= getattr(data, 'interested', None) or ""
            lead_query_ins.query= getattr(data, 'query', None) or ""
            lead_query_ins.state= getattr(data, 'state', None) or ""
            lead_query_ins.country= getattr(data, 'country', None) or ""
            lead_query_ins.tag= NAMES.QUERY_TAG

            try:
                for logs in data.clientLogs:
                    logData={'by':logs.by,'message':logs.message,'date':datetime.now().strftime(NAMES.DMY_HM_FORMAT)}
                    currentLogs = lead_query_ins.clientLogs
                    currentLogs.append(logData)
                    lead_query_ins.clientLogs = currentLogs

            except Exception as e:
                pass
                pass
            
            stage = getattr(data, 'stage', None)
            if stage:
                lead_query_ins.stage = stage
            
            lead_status = getattr(data, 'leadStatus', None)
            if lead_status:
                lead_query_ins.leadStatus = lead_status
            

            if user:
                lead_query_ins.user= user

            leadfor = None
            try:
                if data.type==NAMES.PRODUCT:
                    leadfor = await sync_to_async(Product.objects.get)(id=data.itemId)
                    lead_query_ins.product= leadfor
                elif data.type == NAMES.CATALOUGE:
                    leadfor = await sync_to_async(Catelogue.objects.get)(id=data.itemId)
                    lead_query_ins.catalouge= leadfor
                elif data.type == NAMES.SERVICE:
                    leadfor = await sync_to_async(Service.objects.get)(id=data.itemId)
                    lead_query_ins.service= leadfor
            except Exception as e:
                pass
                pass
            
            if leadfor:
                lead_query_ins.business= leadfor.business
            else:
                # No product/service/catalogue item — link directly to the business
                # the enquiry names (e.g. a reel on a business profile), falling back
                # to the authenticated user's own business.
                business_id = getattr(data, 'businessId', None)
                if business_id:
                    lead_query_ins.business = await sync_to_async(
                        lambda: Business.objects.filter(id=business_id).first())()
                elif user:
                    lead_query_ins.business= user.user_business

            await sync_to_async(lead_query_ins.save)()

            respData = await self.GetLeadQueryTask(lead_query_ins)
            return True,respData
            
        except Exception as e:
            pass
            return None,str(e)
  
    @classmethod
    async def UpdateLeadQueryTask(self, lead_query_ins:LeadQuery, data:LeadQueryUpdateSchema|AdminLeadsUpdateSchema):
        try:
            lead_query_ins.name= getattr(data, NAMES.NAME, None) or lead_query_ins.name
            lead_query_ins.phone= getattr(data, NAMES.PHONE, None) or lead_query_ins.phone
            lead_query_ins.email= getattr(data, NAMES.EMAIL, None) or lead_query_ins.email
            lead_query_ins.interested= getattr(data, NAMES.INTRESTED, None) or lead_query_ins.interested
            lead_query_ins.query= getattr(data, NAMES.QUERY, None) or lead_query_ins.query
            lead_query_ins.state= getattr(data, NAMES.STATE, None) or lead_query_ins.state
            lead_query_ins.country= getattr(data, NAMES.COUNTRY, None) or lead_query_ins.country
            lead_query_ins.status= getattr(data, NAMES.STATUS, None) or lead_query_ins.status
            lead_query_ins.tag= getattr(data, NAMES.TAG, None) or lead_query_ins.tag
            lead_query_ins.priority= getattr(data, NAMES.PRIORITY, None) or lead_query_ins.priority
            lead_query_ins.remark= getattr(data, NAMES.REMARK, None) or lead_query_ins.remark
            lead_query_ins.city= getattr(data, NAMES.CITY, None) or lead_query_ins.city

            try:
                for logs in data.clientLogs:
                    logData={'by':logs.by,'message':logs.message,'date':datetime.now().strftime(NAMES.DMY_HM_FORMAT)}
                    currentLogs = lead_query_ins.clientLogs
                    currentLogs.append(logData)
                    lead_query_ins.clientLogs = currentLogs

            except Exception as e:
                pass
                pass
            
            lead_status = getattr(data, NAMES.LEAD_STATUS, None)
            if lead_status:
                lead_query_ins.leadStatus = lead_status or lead_query_ins.leadStatus
            
            stage = getattr(data, NAMES.STAGE, None)
            if stage:
                lead_query_ins.stage = stage or lead_query_ins.stage
            
            pass
            
            await sync_to_async(lead_query_ins.save)()
            data = await self.GetLeadQueryTask(lead_query_ins)
            return data
            
        except Exception as e:
            pass
            return None

    @classmethod
    async def DeleteLeadQueryTask(self, lead_query_ins:LeadQuery):
        try:
            await sync_to_async(lead_query_ins.delete)()
            return True,True
            
        except Exception as e:
            pass
            return False,
    @classmethod
    async def UpdateLeadQueryStatusTask(self, lead_query_ins:LeadQuery, data:LeadQueryStatusSchema):
        try:
            lead_query_ins.status= data.status            
            await sync_to_async(lead_query_ins.save)()
            data = await self.GetLeadQueryTask(lead_query_ins)
            return data
            
        except Exception as e:
            (f'Error in CreateLeadQueryTask {e}')
            return None

    @classmethod
    async def UpdateLeadQueryPriorityTask(self, lead_query_ins:LeadQuery, data):
        try:
            lead_query_ins.priority= data.priority
            await sync_to_async(lead_query_ins.save)()
            data = await self.GetLeadQueryTask(lead_query_ins)
            return data
            
        except Exception as e:
            (f'Error in CreateLeadQueryTask {e}')
            return None

    @classmethod
    async def UpdateLeadQueryRemarkTask(self, lead_query_ins:LeadQuery, data):
        try:
            lead_query_ins.remark= data.remark            
            await sync_to_async(lead_query_ins.save)()
            data = await self.GetLeadQueryTask(lead_query_ins)
            return data
            
        except Exception as e:
            (f'Error in CreateLeadQueryTask {e}')
            return None


    @classmethod
    async def GetLeadQueryTask(self, lead_query_ins:LeadQuery):
        try:
            assignedbusiness = lead_query_ins.business.businessName if lead_query_ins.business else None
            leadFor:Product = lead_query_ins.product if lead_query_ins.product else lead_query_ins.catalouge if lead_query_ins.catalouge else lead_query_ins.service
            data = {
                NAMES.ID:lead_query_ins.pk,
                NAMES.NAME:lead_query_ins.name, 
                NAMES.PHONE:lead_query_ins.phone, 
                NAMES.EMAIL:lead_query_ins.email, 
                NAMES.INTRESTED:lead_query_ins.interested, 
                NAMES.QUERY:lead_query_ins.query, 
                NAMES.STATE:lead_query_ins.state, 
                NAMES.CITY:lead_query_ins.city, 
                NAMES.COUNTRY:lead_query_ins.country, 
                NAMES.STATUS:lead_query_ins.status, 
                NAMES.TAG:lead_query_ins.tag, 
                NAMES.PRIORITY:lead_query_ins.priority, 
                NAMES.REMARK:lead_query_ins.remark,
                NAMES.DATE:lead_query_ins.timestamp.strftime(NAMES.DMY_FORMAT),
                NAMES.ASSIGNED:assignedbusiness,
                NAMES.LEADFOR:leadFor.title if leadFor else None,
                NAMES.CLIENT_LOGS:lead_query_ins.clientLogs

            }
            return data
            
        except Exception as e:
            pass
            return None


    @classmethod
    async def GetLeadQueriesTask(self,queryParams=None):
        try:
            query_data = []
            async for lead_query in LeadQuery.objects.filter(queryParams).order_by(f'-{NAMES.TIMESTAMP}'):
                data = {
                    NAMES.ID: lead_query.pk,
                    NAMES.NAME: lead_query.name,
                    NAMES.PHONE: lead_query.phone,
                    NAMES.EMAIL: lead_query.email,
                    NAMES.INTRESTED: lead_query.interested,
                    NAMES.QUERY: lead_query.query,
                    NAMES.STATE: lead_query.state,
                    NAMES.COUNTRY: lead_query.country,
                    NAMES.STATUS: lead_query.status,
                    NAMES.TAG: lead_query.tag,
                    NAMES.PRIORITY: lead_query.priority,
                    NAMES.REMARK: lead_query.remark,
                }
                query_data.append(data)

            return query_data

        except Exception as e:
            (f'Error in GetLeadQueryTask: {e}')
            return None

    @classmethod
    async def AssignLeadQueryTask(self,leadQueryIns:LeadQuery,business:Business):
        try:
            leadQueryIns.business = business
            await sync_to_async(leadQueryIns.save)()
            leadData = await self.GetLeadQueryTask(leadQueryIns)
            return leadData
        except Exception as e:
            (f'Error in  AssignLeadQueryTask- {e}')
            return False