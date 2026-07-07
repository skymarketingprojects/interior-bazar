from adrf.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.decorators.ViewDecorator import exceptionHandler

from interior_admin.Controllers.Templates.TemplatesController import TEMPLATES_CONTROLLER
from interior_admin.Controllers.Templates.Validators.TemplatesValidators import TemplateCreateSchema, TemplateUpdateSchema
from interior_admin.Validators.adminValidators import hasAccess


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@exceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=ServerResponse)
async def TemplatesCollectionView(request: Request):
    """GET  /api/v1/admin/templates/  — list all templates.
    POST /api/v1/admin/templates/  — create a template."""
    await hasAccess(request=request)
    if request.method == 'POST':
        return await TEMPLATES_CONTROLLER.Create(payload=TemplateCreateSchema(**request.data))
    return await TEMPLATES_CONTROLLER.List()


@api_view(['PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
@exceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=ServerResponse)
async def TemplateDetailView(request: Request, templateId: int):
    """PUT    /api/v1/admin/templates/<id>/  — update a template.
    DELETE /api/v1/admin/templates/<id>/  — delete a template."""
    await hasAccess(request=request)
    if request.method == 'DELETE':
        return await TEMPLATES_CONTROLLER.Delete(templateId=templateId)
    return await TEMPLATES_CONTROLLER.Update(templateId=templateId, payload=TemplateUpdateSchema(**request.data))
