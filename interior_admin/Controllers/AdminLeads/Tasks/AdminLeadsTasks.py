from asgiref.sync import sync_to_async
from app_ib.Utils.Names import NAMES
from app_ib.models import LeadQuery


class ADMIN_LEADS_TASKS:
    @classmethod
    async def GetLeadQueryTask(self, lead_query_ins:LeadQuery):
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
            
        except Exception as e:
            pass
            return None
