from asgiref.sync import sync_to_async
from app_ib.models import Business
from app_ib.Controllers.Business.Tasks.BusinessTasks import BUSS_TASK
from django.db.models import Q
from django.conf import settings
from app_ib.Utils.AppMode import APPMODE
from app_ib.Utils.MyMethods import MY_METHODS
class PANEL_SEARCH_TASKS:
    
    @classmethod
    async def GetSearchResults(cls, Query):
        try:
            businessResults = None
            if settings.ENV == APPMODE.PROD:
                businessResults = await sync_to_async(
                    lambda: Business.objects.filter(Q(businessName__icontains=Query) | Q(businessSegment__value__icontains=Query),selfCreated = False)
                )()
            else:
                businessResults = await sync_to_async(
                    lambda: Business.objects.filter(Q(businessName__icontains=Query) | Q(businessSegment__value__icontains=Query))
                )()
            results = []

            for business in businessResults:
                businessData = await BUSS_TASK.GetBusinessInfoForSearch(id=business.pk)
                # if businessData is None:
                #     continue
                results.append(businessData)
            await MY_METHODS.printStatus(f'[GetSearchResults]: Found {len(results)} results for query "{Query}"')


            return results
        except Exception as e:
            await MY_METHODS.printStatus(f'[GetSearchResults Error]: {e}')
            return False
