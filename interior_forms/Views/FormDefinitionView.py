"""
Public form-definition views.

Canonical responder stack (memory: ib-engine-view-decorator-conversion): sync
DRF @api_view functions wrapped by @exceptionHandler(responseFunc=ServerResponse);
the decorator maps the controller's NotFound_ to code 410 (not_exist); views
pass the controller's LocalResponse straight through as a ServerResponse.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.decorators.ViewDecorator import exceptionHandler
from interior_forms.Controllers.FormDefinitionController import FORM_DEFINITION_CONTROLLER


@api_view(["GET"])
@permission_classes([AllowAny])
@exceptionHandler(responseFunc=ServerResponse, errorMessage=RESPONSE_MESSAGES.form_definition_fetch_error)
def GetFormDefinitionView(request, key: str):
    local = FORM_DEFINITION_CONTROLLER.getDefinition(key)
    return ServerResponse(response=local.response, code=local.code, message=local.message, data=local.data)
