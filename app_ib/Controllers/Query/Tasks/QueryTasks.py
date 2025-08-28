from asgiref.sync import sync_to_async
from app_ib.models import LeadQuery

class LEAD_QUERY_TASK:

    @classmethod
    async def CreateLeadQueryTask(self, business_ins, data):
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
            print(f'Error in CreateLeadQueryTask {e}')
            return None
  
    @classmethod
    async def UpdateLeadQueryTask(self, lead_query_ins, data):
        try:
            lead_query_ins.name= data.name
            lead_query_ins.phone= data.phone
            lead_query_ins.email= data.email
            lead_query_ins.interested= data.interested            
            lead_query_ins.query= data.query
            lead_query_ins.state= data.state
            lead_query_ins.country= data.country
            lead_query_ins.status= data.status
            lead_query_ins.tag= data.tag
            lead_query_ins.priority= data.priority
            lead_query_ins.remark= data.remark
            
            await sync_to_async(lead_query_ins.save)()
            return True
            
        except Exception as e:
            print(f'Error in CreateLeadQueryTask {e}')
            return None

    @classmethod
    async def UpdateLeadQueryStatusTask(self, lead_query_ins, data):
        try:
            lead_query_ins.status= data.status            
            await sync_to_async(lead_query_ins.save)()
            return True
            
        except Exception as e:
            print(f'Error in CreateLeadQueryTask {e}')
            return None

    @classmethod
    async def UpdateLeadQueryPriorityTask(self, lead_query_ins, data):
        try:
            lead_query_ins.priority= data.priority            
            await sync_to_async(lead_query_ins.save)()
            return True
            
        except Exception as e:
            print(f'Error in CreateLeadQueryTask {e}')
            return None

    @classmethod
    async def UpdateLeadQueryRemarkTask(self, lead_query_ins, data):
        try:
            lead_query_ins.remark= data.remark            
            await sync_to_async(lead_query_ins.save)()
            return True
            
        except Exception as e:
            print(f'Error in CreateLeadQueryTask {e}')
            return None


    @classmethod
    async def GetLeadQueryTask(self, lead_query_ins):
        try:
            data = {
                'name':lead_query_ins.name, 
                'phone':lead_query_ins.phone, 
                'email':lead_query_ins.email, 
                'interested':lead_query_ins.interested, 
                'query':lead_query_ins.query, 
                'state':lead_query_ins.state, 
                'country':lead_query_ins.country, 
                'status':lead_query_ins.status, 
                'tag':lead_query_ins.tag, 
                'priority':lead_query_ins.priority, 
                'remark':lead_query_ins.remark
            }
            return data
            
        except Exception as e:
            print(f'Error in CreateLeadQueryTask {e}')
            return None


    @classmethod
    async def GetLeadQueriesTask(self, business_ins):
        try:
            query_data = []
            async for lead_query in LeadQuery.objects.filter(business=business_ins):
                data = {
                    'id': lead_query.pk,
                    'name': lead_query.name,
                    'phone': lead_query.phone,
                    'email': lead_query.email,
                    'interested': lead_query.interested,
                    'query': lead_query.query,
                    'state': lead_query.state,
                    'country': lead_query.country,
                    'status': lead_query.status,
                    'tag': lead_query.tag,
                    'priority': lead_query.priority,
                    'remark': lead_query.remark,
                }
                query_data.append(data)

            return query_data

        except Exception as e:
            print(f'Error in GetLeadQueryTask: {e}')
            return None
