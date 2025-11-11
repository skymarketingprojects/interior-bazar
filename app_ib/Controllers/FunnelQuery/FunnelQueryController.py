from asgiref.sync import sync_to_async
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.Names import NAMES
from app_ib.Utils.LocalResponse import LocalResponse

from .Tasks.FunnelQueryTasks import FUNNEL_QUERY_TASKS
from .Validators.FunnelQueryValidators import FUNNEL_QUERY_VALIDATORS
from app_ib.models import FunnelForm
from app_ib.Utils.MyMethods import MY_METHODS
from django.core.paginator import Paginator


class FUNNEL_QUERY_CONTROLLER:
    
    @classmethod
    async def CreateFunnelQuery(cls, request):
        try:
            data = request.data
            
            # Create the funnel query
            success, result = await FUNNEL_QUERY_TASKS.CreateFunnelQuery(data)
            if not success:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.funnel_query_create_error,
                    code=RESPONSE_CODES.error,
                    data=result
                )
            
            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.funnel_query_created_success,
                code=RESPONSE_CODES.success,
                data=None
            )
        
        except Exception as e:
            #await MY_METHODS.printStatus(f"Error in CreateFunnelQuery:{str(e)}")
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.funnel_query_create_error,
                code=RESPONSE_CODES.error,
                data=str(e)
            )
    
    # Get Funnel Queries using django default pagination
    @classmethod
    async def GetFunnelQueries(cls,pageNumber, pageSize):
        try:
            forms = await sync_to_async(list)(FunnelForm.objects.all().order_by(f"-{NAMES.TIMESTAMP}"))
            paginator = Paginator(forms, pageSize)
            page_obj = await sync_to_async(paginator.get_page)(pageNumber)
            forms_list = page_obj.object_list
            
            funnel_queries = []
            for form in forms_list:
                success, formData = await FUNNEL_QUERY_TASKS.GetFunnelQueries(form)
                if success:
                    funnel_queries.append(formData)
            
            response_data = {
                NAMES.LEADS: funnel_queries,
                NAMES.TOTAL_PAGES: paginator.num_pages,
                NAMES.CURRENT_PAGE: page_obj.number,
                NAMES.HAS_NEXT: page_obj.has_next(),
                NAMES.HAS_PREVIOUS: page_obj.has_previous(),
                NAMES.TOTAL_ITEMS: paginator.count
            }
            
            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.query_fetch_success,
                code=RESPONSE_CODES.success,
                data=response_data
            )
        except Exception as e:
            #await MY_METHODS.printStatus(f"Error in GetFunnelQueries:{str(e)}")
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.query_fetch_error,
                code=RESPONSE_CODES.error,
                data=str(e)
            )

