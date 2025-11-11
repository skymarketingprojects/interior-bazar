from asgiref.sync import sync_to_async
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.Names import NAMES
from app_ib.Utils.LocalResponse import LocalResponse

from .Tasks.PanelSearchTasks import PANEL_SEARCH_TASKS
from .Validators.PanelSearchValidators import PANEL_SEARCH_VALIDATORS
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.Controllers.Business.Tasks.BusinessTasks import BUSS_TASK

class PANEL_SEARCH_CONTROLLER:
    
    @classmethod
    async def GetSearchResults(cls, Query):
        try:
            results = await PANEL_SEARCH_TASKS.GetSearchResults(Query=Query)
            data = {
                NAMES.BUSINESSES: results
                }
            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message='Search results fetched successfully.',
                code=RESPONSE_CODES.success,
                data=data
            )

        except Exception as e:
            #await MY_METHODS.printStatus(f'[GetSearchResults Error]: {e}')
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message='Failed to fetch search results.',
                code=RESPONSE_CODES.error,
                data={NAMES.ERROR: str(e)}
            )

    @classmethod
    async def GetBusinessByID(cls,Id):
        try:
            business = await BUSS_TASK.GetBusinessInfo(id=Id)
            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message='Business fetched successfully.',
                code=RESPONSE_CODES.success,
                data=business
            )

        except Exception as e:
            #await MY_METHODS.printStatus(f'[GetBusinessByID Error]: {e}')
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message='Failed to fetch business.',
                code=RESPONSE_CODES.error,
                data={NAMES.ERROR: str(e)}
            )