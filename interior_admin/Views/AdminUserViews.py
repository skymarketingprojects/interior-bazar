from interior_admin.Controllers.AdminUser.AdminUserController import ADMIN_USER_CONTROLLER

from adrf.decorators import api_view
from adrf.views import APIView

from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.Names import NAMES,ACCESSLIST
from app_ib.decorators.ViewDecorator import exceptionHandler
from app_ib.Utils.BaseValidator import LocalResponse

from interior_admin.Validators.adminValidators import hasAccess

from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated


class AdminUserViews(APIView):
    permission_classes = [IsAuthenticated]


    @exceptionHandler(
        errorMessage=RESPONSE_MESSAGES.user_fetch_success,
        responseFunc=ServerResponse
    )
    def get(self, request,userId=None):
        hasAccess(user=request.user, accessName=ACCESSLIST.ACCESS_ADMIN)
        resp:LocalResponse = None
        if userId:
            resp = ADMIN_USER_CONTROLLER.GetUserDataController(userId=int(userId))
        else:
            resp = ADMIN_USER_CONTROLLER.getSelfCreatedUsersController(owner=request.user)

        return resp
    

    @exceptionHandler(
        errorMessage=RESPONSE_MESSAGES.user_create_error,
        responseFunc=ServerResponse
    )
    def post(self, request):
        hasAccess(user=request.user, accessName=ACCESSLIST.ACCESS_ADMIN)
        return ADMIN_USER_CONTROLLER.createAdminUserController(
            owner=request.user,
            data=request.data
        )
    
    @exceptionHandler(
        errorMessage=RESPONSE_MESSAGES.user_update_error,
        responseFunc=ServerResponse
    )
    def put(self, request,userId):
        hasAccess(user=request.user, accessName=ACCESSLIST.ACCESS_ADMIN)
        return ADMIN_USER_CONTROLLER.updateAdminUserController(
            owner=request.user,
            userId=userId,
            data=request.data
        )
    
    @exceptionHandler(
        errorMessage=RESPONSE_MESSAGES.user_delete_error,
        responseFunc=ServerResponse
    )
    def delete(self, request,userId):
        hasAccess(user=request.user, accessName=ACCESSLIST.ACCESS_ADMIN)
        return ADMIN_USER_CONTROLLER.deleteAdminUserController(
            owner=request.user,
            userId=userId
        )
    
        