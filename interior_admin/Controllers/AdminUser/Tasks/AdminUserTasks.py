from asgiref.sync import sync_to_async

from django.contrib.auth.hashers import make_password, check_password

from app_ib.Controllers.Profile.ProfileController import PROFILE_CONTROLLER

from rbac_module.Controllers.RoleController.RoleController import ROLE_CONTROLLER

from app_ib.Utils.Names import NAMES
from app_ib.models import CustomUser as User
from app_ib.models import UserProfile

import asyncio

from rbac_module.models import UserCreationAudit, Role
from rbac_module.Controllers.RoleController.Validators.RoleValidators import (
    RoleUpdateSchema,
)


class ADMIN_USER_TASK:

    @classmethod
    async def getUserDataTask(cls, user):
        try:
            profile_data = await PROFILE_CONTROLLER.GetProfileData(user)

            role_access_data = await ROLE_CONTROLLER.getRolesByUserController(user)

            profile_data.data.update(role_access_data.data)

            return profile_data.response, profile_data.data

        except Exception as e:
            return False, str(e)

    @classmethod
    async def GetUserViewDataTask(cls, user):
        try:
            profile_data = await PROFILE_CONTROLLER.GetProfileData(user)
            

            return profile_data.response, profile_data.data

        except Exception as e:
            return {
                NAMES.STATUS: False,
                NAMES.ERROR: str(e)
            }

    @classmethod
    async def createAdminUserTask(cls, owner, data):
        try:
            user = User(
                userType=NAMES.ADMIN,
                is_active=True,
                is_staff=True,
                username=data.username,
                password=make_password(data.password)
            )

            await sync_to_async(user.save)()
            roleschema = RoleUpdateSchema(roles=data.roles)

            tasks = [
                UserProfile(
                    user=user,
                    name=data.name,
                    phone=data.phone,
                    email=data.email,
                ).save(),
                UserCreationAudit(
                    user=user,
                    createdBy=owner
                ).save(),
                ROLE_CONTROLLER.updateRoleController(user, roleschema)
            ]

            await asyncio.gather(*tasks)
            user_data = await cls.getUserDataTask(user)

            return user_data

        except Exception as e:
            return False, str(e)

    @classmethod
    async def updateAdminUser(cls, user, data):
        try:
            for field, value in data.__dict__.items():
                if value is not None:
                    setattr(user, field, value)

            await sync_to_async(user.save)()

            await ROLE_CONTROLLER.updateRoleController(user, RoleUpdateSchema(roles=data.roles))

            user_data = await cls.getUserDataTask(user)

            return user_data

        except Exception as e:
            return False, str(e)


    @classmethod
    async def deleteAdminUser(cls, user: User):
        try:
            await sync_to_async(user.delete)()

            return True, "User deleted successfully"

        except Exception as e:
            return False, str(e)
