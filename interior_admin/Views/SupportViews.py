from adrf.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.decorators.ViewDecorator import exceptionHandler

from interior_admin.Controllers.Support.SupportController import SUPPORT_CONTROLLER
from interior_admin.Controllers.Support.Validators.SupportValidators import SupportListFilters, ReplySchema
from interior_admin.Validators.adminValidators import hasAccess


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@exceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=ServerResponse)
async def ListTicketsView(request: Request):
    """GET /api/v1/admin/support/ — paginated ticket list, filter by status."""
    await hasAccess(request=request)
    return await SUPPORT_CONTROLLER.ListTickets(queryParams=SupportListFilters(**request.query_params.dict()))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@exceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=ServerResponse)
async def GetTicketView(request: Request, ticketId: int):
    """GET /api/v1/admin/support/<id>/ — ticket detail incl. message + replies."""
    await hasAccess(request=request)
    return await SUPPORT_CONTROLLER.GetTicket(ticketId=ticketId)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@exceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=ServerResponse)
async def ReplyTicketView(request: Request, ticketId: int):
    """POST /api/v1/admin/support/<id>/reply/ — append an admin reply."""
    await hasAccess(request=request)
    return await SUPPORT_CONTROLLER.ReplyTicket(ticketId=ticketId, payload=ReplySchema(**request.data), actor=request.user)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@exceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=ServerResponse)
async def CloseTicketView(request: Request, ticketId: int):
    """POST /api/v1/admin/support/<id>/close/ — mark ticket closed."""
    await hasAccess(request=request)
    return await SUPPORT_CONTROLLER.CloseTicket(ticketId=ticketId, actor=request.user)
