from asgiref.sync import sync_to_async
from app_ib.models import LeadQuery
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.Utils.Names import NAMES
from app_ib.models import Business, CustomUser
from interior_products.models import Product, Service, Catelogue
from ..Validators.QueryValidators import LeadQueryCreateSchema, LeadQueryUpdateSchema, LeadQueryStatusSchema
from interior_admin.Controllers.AdminLeads.Validators.AdminLeadsValidators import AdminLeadsCreateSchema, AdminLeadsUpdateSchema
from datetime import datetime

class LEAD_QUERY_TASK:

    @classmethod
    async def CreateLeadQueryTask(cls, data: LeadQueryCreateSchema | AdminLeadsCreateSchema, user: CustomUser = None):
        try:
            lead_query_ins = LeadQuery()
            lead_query_ins.name = getattr(data, 'name', None) or ""
            lead_query_ins.phone = getattr(data, 'phone', None) or ""
            lead_query_ins.email = getattr(data, 'email', None) or ""
            lead_query_ins.interested = getattr(data, 'interested', None) or ""
            lead_query_ins.query = getattr(data, 'query', None) or ""
            lead_query_ins.state = getattr(data, 'state', None) or ""
            lead_query_ins.country = getattr(data, 'country', None) or ""
            lead_query_ins.tag = NAMES.QUERY_TAG

            try:
                for logs in data.clientLogs:
                    logData = {'by': logs.by, 'message': logs.message, 'date': datetime.now().strftime(NAMES.DMY_HM_FORMAT)}
                    currentLogs = lead_query_ins.clientLogs
                    currentLogs.append(logData)
                    lead_query_ins.clientLogs = currentLogs
            except: pass
            
            stage = getattr(data, 'stage', None)
            if stage: lead_query_ins.stage = stage
            
            lead_status = getattr(data, 'leadStatus', None)
            if lead_status: lead_query_ins.leadStatus = lead_status

            if user: lead_query_ins.user = user

            leadfor = None
            try:
                if data.type == NAMES.PRODUCT:
                    leadfor = await sync_to_async(Product.objects.get)(id=data.itemId)
                    lead_query_ins.product = leadfor
                elif data.type == NAMES.CATALOUGE:
                    leadfor = await sync_to_async(Catelogue.objects.get)(id=data.itemId)
                    lead_query_ins.catalouge = leadfor
                elif data.type == NAMES.SERVICE:
                    leadfor = await sync_to_async(Service.objects.get)(id=data.itemId)
                    lead_query_ins.service = leadfor
            except: pass
            
            if leadfor:
                lead_query_ins.business = leadfor.business
            elif user:
                lead_query_ins.business = await sync_to_async(lambda: getattr(user, 'user_business', None))()

            await sync_to_async(lead_query_ins.save)()
            respData = await cls.GetLeadQueryTask(lead_query_ins)
            return True, respData
            
        except Exception as e:
            return None, str(e)

    @classmethod
    async def UpdateLeadQueryTask(cls, lead_query_ins: LeadQuery, data: LeadQueryUpdateSchema | AdminLeadsUpdateSchema):
        try:
            # ... simple field sets
            for attr in [NAMES.NAME, NAMES.PHONE, NAMES.EMAIL, NAMES.INTRESTED, NAMES.QUERY, NAMES.STATE, NAMES.COUNTRY, NAMES.STATUS, NAMES.TAG, NAMES.PRIORITY, NAMES.REMARK, NAMES.CITY]:
                val = getattr(data, attr, None)
                if val: setattr(lead_query_ins, attr, val)

            try:
                for logs in data.clientLogs:
                    logData = {'by': logs.by, 'message': logs.message, 'date': datetime.now().strftime(NAMES.DMY_HM_FORMAT)}
                    currentLogs = lead_query_ins.clientLogs
                    currentLogs.append(logData)
                    lead_query_ins.clientLogs = currentLogs
            except: pass
            
            lead_status = getattr(data, NAMES.LEAD_STATUS, None)
            if lead_status: lead_query_ins.leadStatus = lead_status
            
            stage = getattr(data, NAMES.STAGE, None)
            if stage: lead_query_ins.stage = stage
            
            await sync_to_async(lead_query_ins.save)()
            return await cls.GetLeadQueryTask(lead_query_ins)
        except Exception as e:
            await MY_METHODS.printStatus(f'Error in UpdateLeadQueryTask {str(e)}')
            return None

    @classmethod
    async def DeleteLeadQueryTask(cls, lead_query_ins: LeadQuery):
        try:
            await sync_to_async(lead_query_ins.delete)()
            return True, True
        except: return False, None

    @classmethod
    async def BulkSerializeLeads(cls, lead_list):
        """
        High-performance bulk serialization for LeadQuery instances.
        Replicates exact legacy format.
        """
        results = []
        for lead in lead_list:
            try:
                assigned_business = lead.business.businessName if lead.business else None
                lead_for_obj = lead.product or lead.catalouge or lead.service
                
                results.append({
                    NAMES.ID: lead.pk,
                    NAMES.NAME: lead.name,
                    NAMES.PHONE: lead.phone,
                    NAMES.EMAIL: lead.email,
                    NAMES.INTRESTED: lead.interested,
                    NAMES.QUERY: lead.query,
                    NAMES.STATE: lead.state,
                    NAMES.CITY: lead.city,
                    NAMES.COUNTRY: lead.country,
                    NAMES.STATUS: lead.status,
                    NAMES.TAG: lead.tag,
                    NAMES.PRIORITY: lead.priority,
                    NAMES.REMARK: lead.remark,
                    NAMES.DATE: lead.timestamp.strftime(NAMES.DMY_FORMAT),
                    NAMES.ASSIGNED: assigned_business,
                    NAMES.LEADFOR: lead_for_obj.title if lead_for_obj else None,
                    NAMES.CLIENT_LOGS: lead.clientLogs
                })
            except: pass
        return results

    @classmethod
    async def GetLeadQueryTask(cls, lead_query_ins: LeadQuery):
        """
        Individual fetch using the same bulk logic for consistency.
        """
        # Ensure relationships are loaded if possible, otherwise bulk logic handles it
        data_list = await cls.BulkSerializeLeads([lead_query_ins])
        return data_list[0] if data_list else None

    @classmethod
    async def GetLeadQueriesTask(cls, queryParams=None):
        """
        Optimized bulk fetch for LeadQuery lists.
        """
        try:
            # Apply select_related to avoid N+1 queries during serialization
            queryset = LeadQuery.objects.filter(queryParams).select_related(
                'business', 'product', 'catalouge', 'service'
            ).order_by(f'-{NAMES.TIMESTAMP}')
            
            lead_list = await sync_to_async(list)(queryset)
            return await cls.BulkSerializeLeads(lead_list)
        except Exception as e:
            print(f'Error in GetLeadQueriesTask: {e}')
            return None

    @classmethod
    async def AssignLeadQueryTask(cls, leadQueryIns: LeadQuery, business: Business):
        try:
            leadQueryIns.business = business
            await sync_to_async(leadQueryIns.save)()
            return await cls.GetLeadQueryTask(leadQueryIns)
        except: return False