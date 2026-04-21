from asgiref.sync import sync_to_async
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.Utils.Names import NAMES
from app_ib.Utils.MyMethods import MY_METHODS

from .Tasks.AdminUserTasks import ADMIN_USER_TASK
# from .Validators.AdminUserValidators import ADMIN_USER_VALIDATORS
from rbac_module.models import UserCreationAudit

from app_ib.models import CustomUser

from interior_admin.Validators.adminValidators import CreateAdminUser,UpdateAdminUser

class ADMIN_USER_CONTROLLER:

    ###########################################
    # Get User Data by User ID
    ###########################################
    @classmethod
    async def GetUserDataController(cls, userId: int):
        try:
            user_ins = await sync_to_async(CustomUser.objects.get)(id=userId)

            status,task_resp = await ADMIN_USER_TASK.getUserDataTask(user=user_ins)

            if status:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.success,
                    message=RESPONSE_MESSAGES.user_fetch_success,
                    code=RESPONSE_CODES.success,
                    data=task_resp
                )

            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.user_fetch_error,
                code=RESPONSE_CODES.error,
                data={}
            )

        except CustomUser.DoesNotExist:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.user_not_found,
                code=RESPONSE_CODES.not_exist,
                data={}
            )

        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.user_fetch_error,
                code=RESPONSE_CODES.error,
                data={NAMES.ERROR: str(e)}
            )

    ###########################################
    # Get Users Created by Owner
    ###########################################
    @classmethod
    async def getSelfCreatedUsersController(cls, owner: CustomUser, role=None):
        try:

            created_user_ids = UserCreationAudit.objects.filter(
                createdBy=owner
            ).values_list('user__id', flat=True)

            users_qs = CustomUser.objects.filter(id__in=created_user_ids)

            if role:
                users_qs = users_qs.filter(type=role)

            users_list = await sync_to_async(list)(users_qs)

            users_data = []
            for user in users_list:
                status,task_resp = await ADMIN_USER_TASK.GetUserViewDataTask(user=user)
                if status:
                    users_data.append(task_resp)

            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                message=RESPONSE_MESSAGES.user_fetch_success,
                code=RESPONSE_CODES.success,
                data=users_data
            )

        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.user_fetch_error,
                code=RESPONSE_CODES.error,
                data={NAMES.ERROR: str(e)}
            )

    ###########################################
    # Create Admin User
    ###########################################
    @classmethod
    async def createAdminUserController(cls, owner, data:CreateAdminUser):
        try:
            status,task_resp = await ADMIN_USER_TASK.createAdminUserTask(
                owner=owner,
                data=data
            )
            pass

            if status:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.success,
                    message=RESPONSE_MESSAGES.user_create_success,
                    code=RESPONSE_CODES.success,
                    data=task_resp
                )

            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.user_create_error,
                code=RESPONSE_CODES.error,
                data={}
            )

        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.user_create_error,
                code=RESPONSE_CODES.error,
                data={NAMES.ERROR: str(e)}
            )

    ###########################################
    # Update Admin User
    ###########################################
    @classmethod
    async def updateAdminUserController(cls, owner, userId, data:UpdateAdminUser):
        try:
            is_authorized = UserCreationAudit.objects.filter(
                createdBy=owner,
                user__id=userId
            ).exists()

            if not is_authorized:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.unauthorized,
                    code=RESPONSE_CODES.error,
                    data={}
                )

            user_ins = await sync_to_async(
                lambda: CustomUser.objects.get(id=userId)
                if isinstance(userId, int)
                else CustomUser.objects.get(username=userId)
            )()

            status,task_resp = await ADMIN_USER_TASK.updateAdminUser(
                user=user_ins,
                data=data
            )

            if status:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.success,
                    message=RESPONSE_MESSAGES.user_update_success,
                    code=RESPONSE_CODES.success,
                    data=task_resp
                )

            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.user_update_error,
                code=RESPONSE_CODES.error,
                data={NAMES.ERROR: str(task_resp)}
            )

        except CustomUser.DoesNotExist:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.user_not_found,
                code=RESPONSE_CODES.not_exist,
                data={}
            )

        except Exception as e:
            pass
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.user_update_error,
                code=RESPONSE_CODES.error,
                data={NAMES.ERROR: str(e)}
            )

    ###########################################
    # Delete Admin User
    ###########################################
    @classmethod
    async def deleteAdminUserController(cls, owner, userId):
        try:
            is_authorized = UserCreationAudit.objects.filter(
                created_by=owner,
                user__id=userId
            ).exists()

            if not is_authorized:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.unauthorized,
                    code=RESPONSE_CODES.error,
                    data={}
                )

            user_ins = await sync_to_async(
                lambda: CustomUser.objects.get(id=userId)
                if isinstance(userId, int)
                else CustomUser.objects.get(username=userId)
            )()

            task_resp = await ADMIN_USER_TASK.deleteAdminUser(user=user_ins)

            if task_resp.get(NAMES.STATUS):
                return LocalResponse(
                    response=RESPONSE_MESSAGES.success,
                    message=RESPONSE_MESSAGES.user_delete_success,
                    code=RESPONSE_CODES.success,
                    data={}
                )

            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.user_delete_error,
                code=RESPONSE_CODES.error,
                data={}
            )

        except CustomUser.DoesNotExist:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.user_not_found,
                code=RESPONSE_CODES.not_exist,
                data={}
            )

        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.user_delete_error,
                code=RESPONSE_CODES.error,
                data={NAMES.ERROR: str(e)}
            )

    ###########################################
    # Send User Credentials
    ###########################################
    @classmethod
    async def sendUserCredentialsController(cls, owner, userId):
        try:
            # Check if owner is authorized (created this user)
            is_authorized = await sync_to_async(UserCreationAudit.objects.filter(
                createdBy=owner,
                user__id=userId
            ).exists)()

            if not is_authorized:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.unauthorized,
                    code=RESPONSE_CODES.error,
                    data={}
                )

            user_ins = await sync_to_async(CustomUser.objects.get)(id=userId)

            status, msg = await ADMIN_USER_TASK.sendUserCredentialsTask(user=user_ins)

            if status:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.success,
                    message=msg,
                    code=RESPONSE_CODES.success,
                    data={}
                )

            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=msg,
                code=RESPONSE_CODES.error,
                data={}
            )

        except CustomUser.DoesNotExist:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.user_not_found,
                code=RESPONSE_CODES.not_exist,
                data={}
            )

        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=str(e),
                code=RESPONSE_CODES.error,
                data={NAMES.ERROR: str(e)}
            )
