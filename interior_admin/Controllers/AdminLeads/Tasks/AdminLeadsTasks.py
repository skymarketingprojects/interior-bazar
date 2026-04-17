from asgiref.sync import sync_to_async
from app_ib.Utils.Names import NAMES
from app_ib.models import LeadQuery


class ADMIN_LEADS_TASKS:

    @classmethod
    async def BulkSerializeLeadQueries(cls, lead_queries: list):
        """
        High performance bulk serializer for LeadQuery objects.
        Expects .select_related('business') for maximum speed.
        """
        if not lead_queries:
            return []
            
        serialized_data = []
        for lead in lead_queries:
            try:
                # Pre-calculating fields to avoid repeated lookups
                assigned_business = lead.business.businessName if lead.business else None
                
                item = {
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
                    NAMES.CATEGORY: lead.category,
                    NAMES.PRIORITY: lead.priority,
                    NAMES.REMARK: lead.remark,
                    NAMES.LOGS: lead.logs,
                    NAMES.DATE: lead.timestamp.strftime(NAMES.DMY_FORMAT) if lead.timestamp else None,
                    NAMES.UPDATED_AT: lead.updatedAt.strftime(NAMES.DMY_FORMAT) if lead.updatedAt else None,
                    NAMES.ASSIGNED: assigned_business,
                    NAMES.LEAD_STATUS: lead.leadStatus,
                    NAMES.STAGE: lead.stage,
                    NAMES.CLIENT_LOGS: lead.clientLogs
                }
                serialized_data.append(item)
            except Exception:
                continue
                
        return serialized_data

    @classmethod
    async def GetLeadQueryTask(cls, lead_query_ins:LeadQuery):
        """ Legacy support for single item serialization """
        try:
            assignedbusiness = lead_query_ins.business.businessName if lead_query_ins.business else None
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
                NAMES.CATEGORY:lead_query_ins.category,
                NAMES.PRIORITY:lead_query_ins.priority, 
                NAMES.REMARK:lead_query_ins.remark,
                NAMES.LOGS:lead_query_ins.logs,
                NAMES.DATE:lead_query_ins.timestamp.strftime(NAMES.DMY_FORMAT),
                NAMES.UPDATED_AT:lead_query_ins.updatedAt.strftime(NAMES.DMY_FORMAT),
                NAMES.ASSIGNED:assignedbusiness,
                NAMES.LEAD_STATUS:lead_query_ins.leadStatus,
                NAMES.STAGE:lead_query_ins.stage,
                NAMES.CLIENT_LOGS:lead_query_ins.clientLogs

            }
            return data
            
        except Exception:
            return None
