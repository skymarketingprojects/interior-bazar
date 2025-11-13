import asyncio
from app_ib.Utils.MyMethods import MY_METHODS
from adrf.decorators import api_view
from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.Names import NAMES
from app_ib.Controllers.Contact.ContactController import CONTACT_CONTROLLER
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated

@api_view(['POST'])
async def CreateContactView(request):
    try:
        await MY_METHODS.printStatus('create contact view request.data', request.data)
        data = MY_METHODS.json_to_object(request.data)
        await MY_METHODS.printStatus(f'create contact view data {data}')

        create_contact_resp = await CONTACT_CONTROLLER.CreateContact(data=data)
        await MY_METHODS.printStatus(f'create contact resp {create_contact_resp}')

        return ServerResponse(
            response=create_contact_resp.response,
            message=create_contact_resp.message,
            code=create_contact_resp.code,
            data=create_contact_resp.data
        )

    except Exception as e:
        return ServerResponse(
            response=RESPONSE_MESSAGES.error,
            message=RESPONSE_MESSAGES.contact_generate_error,
            code=RESPONSE_CODES.error,
            data={
                NAMES.ERROR: str(e)
            }
        )