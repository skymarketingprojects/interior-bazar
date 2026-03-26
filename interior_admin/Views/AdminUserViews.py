from interior_admin.Controllers.AdminUser.AdminUserController import ADMIN_USER_CONTROLLER

from adrf.decorators import api_view
from adrf.views import APIView

from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.Names import NAMES,ACCESSLIST
from app_ib.decorators.ViewDecorator import exceptionHandler
from app_ib.Utils.BaseValidator import LocalResponse
from app_ib.Utils.MyMethods import MY_METHODS

from interior_admin.Validators.adminValidators import hasAccess,CreateAdminUser,UpdateAdminUser

from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

class AdminUserViews(APIView):
    permission_classes = [IsAuthenticated]


    @exceptionHandler(
        errorMessage=RESPONSE_MESSAGES.user_fetch_success,
        responseFunc=ServerResponse
    )
    async def get(self, request:Request,userId=None):
        await hasAccess(user=request.user, accessName=ACCESSLIST.ACCESS_ADMIN)
        resp:LocalResponse = None
        if userId:
            resp = await ADMIN_USER_CONTROLLER.GetUserDataController(userId=int(userId))
        else:
            resp = await ADMIN_USER_CONTROLLER.getSelfCreatedUsersController(owner=request.user)

        return resp
    

    @exceptionHandler(
        errorMessage=RESPONSE_MESSAGES.user_create_error,
        responseFunc=ServerResponse
    )
    async def post(self, request:Request):
        await hasAccess(user=request.user, accessName=ACCESSLIST.ACCESS_ADMIN)

        data = CreateAdminUser(**request.data)
        resp  = await ADMIN_USER_CONTROLLER.createAdminUserController(
            owner=request.user,
            data=data
        )
        return resp
    
    @exceptionHandler(
        errorMessage=RESPONSE_MESSAGES.user_update_error,
        responseFunc=ServerResponse
    )
    async def put(self, request:Request,userId):
        await hasAccess(user=request.user, accessName=ACCESSLIST.ACCESS_ADMIN)
        data = UpdateAdminUser(**request.data)
        resp = await ADMIN_USER_CONTROLLER.updateAdminUserController(
            owner=request.user,
            userId=userId,
            data=data
        )
        await MY_METHODS.printStatus(resp)
        return resp
    
    @exceptionHandler(
        errorMessage=RESPONSE_MESSAGES.user_delete_error,
        responseFunc=ServerResponse
    )
    async def delete(self, request:Request,userId):
        await hasAccess(user=request.user, accessName=ACCESSLIST.ACCESS_ADMIN)
        resp = await ADMIN_USER_CONTROLLER.deleteAdminUserController(
            owner=request.user,
            userId=userId
        )
        return resp
    
        
class SendUserCredentialsView(APIView):
    permission_classes = [IsAuthenticated]

    @exceptionHandler(
        errorMessage="Error sending credentials email",
        responseFunc=ServerResponse
    )
    async def post(self, request:Request,userId):
        await hasAccess(user=request.user, accessName=ACCESSLIST.ACCESS_ADMIN)
        resp = await ADMIN_USER_CONTROLLER.sendUserCredentialsController(
            owner=request.user,
            userId=userId
        )
        return resp
