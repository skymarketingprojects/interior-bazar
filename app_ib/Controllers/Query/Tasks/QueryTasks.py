from asgiref.sync import sync_to_async
from app_ib.models import LeadQuery
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.Utils.Names import NAMES
from app_ib.models import Business,CustomUser
from interior_products.models import Product,Service,Catelogue
from ..Validators.QueryValidators import LeadQueryCreateSchema,LeadQueryUpdateSchema,LeadQueryStatusSchema
from interior_admin.Controllers.AdminLeads.Validators.AdminLeadsValidators import AdminLeadsCreateSchema,AdminLeadsUpdateSchema
from datetime import datetime

def _detect_anomaly(name: str, phone: str):
    """Cheap anomaly checks run at lead creation (task 14). Returns a short reason
    slug if the lead looks fake/garbage, else None. Tunable heuristics."""
    digits = "".join(ch for ch in (phone or "") if ch.isdigit())
    # ponytail: India 10-digit; widen to 10-12 for country code if needed
    if len(digits) != 10:
        return "phone_digits"
    n = (name or "").strip()
    # ponytail: trivial-name heuristic; tune thresholds if false positives appear
    if len(n) < 3:
        return "name_trivial"
    if any(ch.isdigit() for ch in n):
        return "name_has_digits"
    lower = n.lower()
    if not any(v in lower for v in "aeiou"):
        return "name_no_vowel"
    letters = [c for c in lower if c.isalpha()]
    if letters and len(set(letters)) == 1:  # 'aaa', 'xxxx'
        return "name_repeated_char"
    return None


class LEAD_QUERY_TASK:

    @classmethod
    async def _score_and_tier(self, lead: LeadQuery):
        """Additive qualification score from the weights singleton → tier via the
        tier_* thresholds (task 15). Read QualificationWeightConfig directly to
        avoid a controller import cycle.
        # ponytail: urgency_* weights are intentionally NOT applied — LeadQuery has
        # no timeline/urgency capture field to source them. Score = contact +
        # genuineness + detail; add a timeline field later to honor urgency sliders."""
        from interior_admin.Controllers.Weights.WeightsController import DEFAULT_WEIGHTS, merged_weights
        try:
            from interior_admin.models import QualificationWeightConfig
            cfg, _ = await QualificationWeightConfig.objects.aget_or_create(id=1)
            w = merged_weights(cfg.weights)
        except Exception:
            w = dict(DEFAULT_WEIGHTS)

        def num(key):
            try:
                return float(w.get(key, DEFAULT_WEIGHTS.get(key, 0)))
            except (TypeError, ValueError):
                return float(DEFAULT_WEIGHTS.get(key, 0))

        phone_digits = "".join(ch for ch in (lead.phone or "") if ch.isdigit())
        name = (lead.name or "").strip()
        text = f"{lead.query or ''} {lead.interested or ''}".strip()

        score = 0.0
        if len(phone_digits) >= 10:  # contact present
            score += num("contact")
        if len(name) >= 3 and any(v in name.lower() for v in "aeiou"):  # genuine-looking
            score += num("genuineness")
        if len(text) >= 20:  # detailed enquiry
            score += num("detail")

        score = round(score)
        if score >= num("tier_A"):
            tier = "A"
        elif score >= num("tier_B"):
            tier = "B"
        elif score >= num("tier_C"):
            tier = "C"
        elif score >= num("tier_D"):
            tier = "D"
        else:
            tier = "E"
        return score, tier

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
            # Admin-authored leads carry these too (public schema omits them →
            # getattr yields None → "" default). Without this the ported Add-lead
            # form silently dropped city/status/priority/remark.
            lead_query_ins.city= getattr(data, 'city', None) or ""
            _status = getattr(data, 'status', None)
            if _status:
                lead_query_ins.status = _status
            lead_query_ins.priority= getattr(data, 'priority', None) or ""
            lead_query_ins.remark= getattr(data, 'remark', None) or ""
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

            # Anomaly gate (task 14): fake phone / gibberish name → quarantine,
            # reason packed into remark. ponytail: reason in remark; add a reason
            # column only if reasons need filtering.
            anomaly = _detect_anomaly(lead_query_ins.name, lead_query_ins.phone)
            if anomaly:
                lead_query_ins.status = 'quarantine'
                lead_query_ins.remark = f"quarantine:{anomaly}"

            # Qualification score+tier computed ONCE here (creation-only).
            lead_query_ins.score, lead_query_ins.tier = await self._score_and_tier(lead_query_ins)

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