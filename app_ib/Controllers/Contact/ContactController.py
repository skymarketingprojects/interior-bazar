from asgiref.sync import sync_to_async
from adrf.decorators import api_view
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.models import Feedback
from app_ib.Controllers.Contact.Tasks.ContactTasks import CONTACT_TASKS

class CONTACT_CONTROLLER:

    @classmethod
    async def CreateContact(self,data):
        try:
            # Test Data
            # print(f'name: {data.contact}')
            # print(f'name: {data.feedback}')

            contact_create_resp_data = await CONTACT_TASKS.CreateContactTask(data=data)
            print(f'create query resp {contact_create_resp_data}')

            if contact_create_resp_data:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.success,
                    message=RESPONSE_MESSAGES.contact_generate_success,
                    code=RESPONSE_CODES.success,
                    data={})

            else:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.contact_generate_error,
                    code=RESPONSE_CODES.error,
                    data={})

        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.contact_generate_error,
                code=RESPONSE_CODES.error,
                data={
                    'error': str(e)
                })

