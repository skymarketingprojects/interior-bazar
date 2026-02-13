from asgiref.sync import sync_to_async
from app_ib.models import LeadQuery
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.Utils.Names import NAMES
from app_ib.models import Business,CustomUser
from interior_products.models import Product,Service,Catelogue
from ..Validators.QueryValidators import LeadQueryCreateSchema,LeadQueryUpdateSchema,LeadQueryStatusSchema
class LEAD_QUERY_TASK:

    @classmethod
    async def CreateLeadQueryTask(self, data:LeadQueryCreateSchema,user:CustomUser=None):
        try:
            lead_query_ins = LeadQuery()

            # using getattr to not get error when field is absent
            lead_query_ins.name= data.name
            lead_query_ins.phone=data.phone
            lead_query_ins.email= data.email
            lead_query_ins.interested= data.interested 
            lead_query_ins.query= data.query
            lead_query_ins.state= data.state
            lead_query_ins.country= data.country
            lead_query_ins.tag= NAMES.QUERY_TAG
            (f'type {data.type}')

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
                # await MY_METHODS.printStatus(f'type or id not found {str(e)}')
                pass
            
            if leadfor:
                lead_query_ins.business= leadfor.business
            elif user:
                lead_query_ins.business= user.user_business

            await sync_to_async(lead_query_ins.save)()

            respData = await self.GetLeadQueryTask(lead_query_ins)
            return True,respData
            
        except Exception as e:
            # await MY_METHODS.printStatus(f'Error in CreateLeadQueryTask {e}')
            return None,str(e)
  
    @classmethod
    async def UpdateLeadQueryTask(self, lead_query_ins:LeadQuery, data:LeadQueryUpdateSchema):
        try:
            lead_query_ins.name= data.name or lead_query_ins.name
            lead_query_ins.phone= data.phone or lead_query_ins.phone
            lead_query_ins.email= data.email or lead_query_ins.email
            lead_query_ins.interested= data.interested or lead_query_ins.interested
            lead_query_ins.query= data.query or lead_query_ins.query
            lead_query_ins.state= data.state or lead_query_ins.state
            lead_query_ins.country= data.country or lead_query_ins.country
            lead_query_ins.status= data.status or lead_query_ins.status
            lead_query_ins.tag= data.tag or lead_query_ins.tag
            lead_query_ins.priority= data.priority or lead_query_ins.priority
            lead_query_ins.remark= data.remark or lead_query_ins.remark
            
            # await MY_METHODS.printStatus(f'tag {data.tag}')
            
            await sync_to_async(lead_query_ins.save)()
            data = await self.GetLeadQueryTask(lead_query_ins)
            return data
            
        except Exception as e:
            # await MY_METHODS.printStatus(f'Error in UpdateLeadQueryTask {str(e)}')
            return None

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
                NAMES.LEADFOR:leadFor.title if leadFor else None

            }
            return data
            
        except Exception as e:
            # await MY_METHODS.printStatus(f'Error in CreateLeadQueryTask {e}')
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