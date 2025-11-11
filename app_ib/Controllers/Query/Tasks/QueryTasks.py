from asgiref.sync import sync_to_async
from app_ib.models import LeadQuery
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.Utils.Names import NAMES
from app_ib.models import Business

class LEAD_QUERY_TASK:

    @classmethod
    async def CreateLeadQueryTask(self, business_ins:Business, data:dict):
        try:
            lead_query_ins = LeadQuery()
            lead_query_ins.business= business_ins
            lead_query_ins.name= data.name
            lead_query_ins.phone= data.phone
            lead_query_ins.email= data.email
            lead_query_ins.interested= data.interested            
            lead_query_ins.query= data.query
            lead_query_ins.state= data.state
            lead_query_ins.country= data.country
            
            await sync_to_async(lead_query_ins.save)()
            return True
            
        except Exception as e:
            #await MY_METHODS.printStatus(f'Error in CreateLeadQueryTask {e}')
            return None
  
    @classmethod
    async def UpdateLeadQueryTask(self, lead_query_ins:LeadQuery, data):
        try:
            lead_query_ins.name= getattr(data, NAMES.NAME, lead_query_ins.name)
            lead_query_ins.phone= getattr(data, NAMES.PHONE, lead_query_ins.phone)
            lead_query_ins.email= getattr(data, NAMES.EMAIL, lead_query_ins.email)
            lead_query_ins.interested= getattr(data, NAMES.INTRESTED, lead_query_ins.interested)
            lead_query_ins.query=getattr(data, NAMES.QUERY, lead_query_ins.query)
            lead_query_ins.state= getattr(data, NAMES.STATE, lead_query_ins.state)
            lead_query_ins.country= getattr(data, NAMES.COUNTRY, lead_query_ins.country)
            lead_query_ins.status= getattr(data, NAMES.STATUS, lead_query_ins.status)
            lead_query_ins.tag= getattr(data, NAMES.TAG, lead_query_ins.tag)
            lead_query_ins.priority= getattr(data, NAMES.PRIORITY, lead_query_ins.priority)
            lead_query_ins.remark= getattr(data, NAMES.REMARK, lead_query_ins.remark)
            
            await sync_to_async(lead_query_ins.save)()
            return True
            
        except Exception as e:
            #await MY_METHODS.printStatus(f'Error in CreateLeadQueryTask {e}')
            return None

    @classmethod
    async def UpdateLeadQueryStatusTask(self, lead_query_ins:LeadQuery, data):
        try:
            lead_query_ins.status= data.status            
            await sync_to_async(lead_query_ins.save)()
            return True
            
        except Exception as e:
            #await MY_METHODS.printStatus(f'Error in CreateLeadQueryTask {e}')
            return None

    @classmethod
    async def UpdateLeadQueryPriorityTask(self, lead_query_ins:LeadQuery, data):
        try:
            lead_query_ins.priority= data.priority            
            await sync_to_async(lead_query_ins.save)()
            return True
            
        except Exception as e:
            #await MY_METHODS.printStatus(f'Error in CreateLeadQueryTask {e}')
            return None

    @classmethod
    async def UpdateLeadQueryRemarkTask(self, lead_query_ins:LeadQuery, data):
        try:
            lead_query_ins.remark= data.remark            
            await sync_to_async(lead_query_ins.save)()
            return True
            
        except Exception as e:
            #await MY_METHODS.printStatus(f'Error in CreateLeadQueryTask {e}')
            return None


    @classmethod
    async def GetLeadQueryTask(self, lead_query_ins:LeadQuery):
        try:
            assignedbusiness = lead_query_ins.business.business_name if lead_query_ins.business else None
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
                NAMES.ASSIGNED:assignedbusiness

            }
            return data
            
        except Exception as e:
            #await MY_METHODS.printStatus(f'Error in CreateLeadQueryTask {e}')
            return None


    @classmethod
    async def GetLeadQueriesTask(self, business_ins:Business):
        try:
            query_data = []
            async for lead_query in LeadQuery.objects.filter(business=business_ins):
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
            #await MY_METHODS.printStatus(f'Error in GetLeadQueryTask: {e}')
            return None

    @classmethod
    async def AssignLeadQueryTask(self,leadQueryIns:LeadQuery,business:Business):
        try:
            leadQueryIns.business = business
            await sync_to_async(leadQueryIns.save)()
            leadData = await self.GetLeadQueryTask(leadQueryIns)
            return leadData
        except Exception as e:
            #await MY_METHODS.printStatus(f'Error in  AssignLeadQueryTask- {e}')
            return False