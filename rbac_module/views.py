from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from adrf.views import APIView as AsyncAPIView
from adrf.decorators import api_view

from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ServerResponse import ServerResponse
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.decorators.ViewDecorator import exceptionHandler

from rbac_module.Controllers.RoleController.RoleController import ROLE_CONTROLLER
from rbac_module.Controllers.RoleController.Validators.RoleValidators import (
    RoleCreateSchema,
    RoleUpdateSchema,
    RoleAccessUpdateSchema,
    RoleAssignUsersSchema
)


class RoleCollectionView(AsyncAPIView):
    permission_classes = [IsAuthenticated]

    @exceptionHandler(
        errorMessage=RESPONSE_MESSAGES.role_list_fetch_error,
        responseFunc=ServerResponse
    )
    async def get(self, request: Request) -> ServerResponse:

        result = await ROLE_CONTROLLER.getRolesByOwnerController(
            user=request.user
        )

        return result


    @exceptionHandler(
        errorMessage=RESPONSE_MESSAGES.role_create_error,
        responseFunc=ServerResponse
    )
    async def post(self, request: Request) -> ServerResponse:

        validated = RoleCreateSchema(**request.data)

        result = await ROLE_CONTROLLER.createRoleController(
            payload=validated.dict(),
            owner=request.user
        )

        return result


    @exceptionHandler(
        errorMessage=RESPONSE_MESSAGES.role_update_error,
        responseFunc=ServerResponse
    )
    async def put(self, request: Request, roleId: int) -> ServerResponse:

        validated = RoleUpdateSchema(**request.data)

        result = await ROLE_CONTROLLER.updateRoleController(
            user=request.user,
            roleId=roleId,
            payload=validated
        )

        return result


    @exceptionHandler(
        errorMessage=RESPONSE_MESSAGES.role_delete_error,
        responseFunc=ServerResponse
    )
    async def delete(self, request: Request, roleId: int) -> ServerResponse:

        result = await ROLE_CONTROLLER.deleteRoleController(
            user=request.user,
            roleId=roleId
        )

        return result


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
@exceptionHandler(
    errorMessage=RESPONSE_MESSAGES.role_update_error,
    responseFunc=ServerResponse
)
async def removeAccessView(request: Request, roleId: int) -> ServerResponse:

    validated = RoleAccessUpdateSchema(**request.data)

    result = await ROLE_CONTROLLER.removeAccessFromRoleController(
        user=request.user,
        roleId=roleId,
        payload=validated
    )

    return result


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
@exceptionHandler(
    errorMessage=RESPONSE_MESSAGES.role_update_error,
    responseFunc=ServerResponse
)
async def removeUserView(request: Request, roleId: int) -> ServerResponse:

    validated = RoleAssignUsersSchema(**request.data)

    result = await ROLE_CONTROLLER.removeUserFromRoleController(
        user=request.user,
        roleId=roleId,
        payload=validated
    )

    return result
