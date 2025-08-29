import asyncio
from app_ib.Utils.MyMethods import MY_METHODS
from adrf.decorators import api_view
from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Controllers.Pages.PagesController import PAGE_CONTROLLER
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated