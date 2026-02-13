from asgiref.sync import sync_to_async
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.Utils.Names import NAMES
from app_ib.decorators.ViewDecorator import controllerExceptionHandler

from .Tasks.FinanceTasks import FINANCE_TASKS
# from .Validators.FinanceValidators import FINANCE_VALIDATORS


class FINANCE_CONTROLLER:

    @classmethod
    @controllerExceptionHandler(
        errorMessage=RESPONSE_MESSAGES.finance_fetch_error,
        responseFunc=LocalResponse,
        successMessage=RESPONSE_MESSAGES.finance_fetch_success
    )
    async def GetFinanceData(cls):
        resp = await FINANCE_TASKS.GetFinanceTableTask()
        return resp
    

