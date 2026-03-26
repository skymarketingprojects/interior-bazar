from asgiref.sync import sync_to_async

from django.contrib.auth.hashers import make_password, check_password

from app_ib.Controllers.Profile.ProfileController import PROFILE_CONTROLLER

from rbac_module.Controllers.RoleController.RoleController import ROLE_CONTROLLER

from app_ib.Utils.Names import NAMES
from app_ib.models import CustomUser as User
from app_ib.models import UserProfile

from interior_admin.Validators.adminValidators import CreateAdminUser,UpdateAdminUser

import asyncio
from django.conf import settings
from interior_notification.Controllers.Publish import publishEmailToUser

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

            profile_data.data['roles'] = role_access_data.data

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
    async def createAdminUserTask(cls, owner, data: CreateAdminUser):
        try:
            # Create user
            user = User(
                type=NAMES.ADMIN,
                is_active=True,
                is_staff=True,
                username=data.username,
                password=make_password(data.password),
                text_password=data.password
            )

            await sync_to_async(user.save)()

            # Create profile & audit in parallel
            await asyncio.gather(
                sync_to_async(UserProfile.objects.create)(
                    user=user,
                    name=data.name,
                    phone=data.phone,
                    email=data.email,
                ),
                sync_to_async(UserCreationAudit.objects.create)(
                    user=user,
                    createdBy=owner
                )
            )

            # ✅ Fetch all roles in one query
            roles = await sync_to_async(list)(
                Role.objects.filter(id__in=data.roles)
            )

            # ✅ Add user to all roles
            if roles:
                await sync_to_async(user.roles.add)(*roles)

            user_data = await cls.getUserDataTask(user)

            return user_data

        except Exception as e:
            return False, str(e)


    @classmethod
    async def updateAdminUser(cls, user, data:UpdateAdminUser):
        try:
            # Update CustomUser fields
            if data.username is not None:
                user.username = data.username
            if data.password is not None:
                user.password = make_password(data.password)
                user.text_password = data.password

            await sync_to_async(user.save)()

            # Update UserProfile fields
            profile_updates = {}
            if data.name is not None:
                profile_updates[NAMES.NAME] = data.name
            if data.phone is not None:
                profile_updates[NAMES.PHONE] = data.phone
            if data.email is not None:
                profile_updates[NAMES.EMAIL] = data.email
            
            if profile_updates:
                profile, created = await sync_to_async(UserProfile.objects.get_or_create)(user=user)
                for field, value in profile_updates.items():
                    setattr(profile, field, value)
                await sync_to_async(profile.save)()

            # Update roles
            if data.roles is not None:
                roles = await sync_to_async(list)(
                    Role.objects.filter(id__in=data.roles)
                )
                await sync_to_async(user.roles.set)(roles)

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


    @classmethod
    async def sendUserCredentialsTask(cls, user: User):
        try:
            # Get profile for email
            profile = await sync_to_async(UserProfile.objects.get)(user=user)
            
            if not profile.email:
                return False, "User email not found in profile"

            subject = "Your Login Credentials"
            html_body = f"""
            <html>
                <body>
                    <h2>Hello {profile.name or user.username},</h2>
                    <p>Your account has been set up with the following credentials:</p>
                    <p><strong>Username:</strong> {user.username}</p>
                    <p><strong>Password:</strong> {user.text_password or 'Test@123'}</p>
                    <br>
                    <p>Please log in and change your password for security.</p>
                </body>
            </html>
            """
            
            # Send email using SES via notification module
            response = await sync_to_async(publishEmailToUser)(
                senderEmail=settings.DEFAULT_FROM_EMAIL,
                recipientEmail=profile.email,
                subject=subject,
                htmlBody=html_body
            )

            if response:
                return True, "Credentials email sent successfully"
            
            return False, "Failed to send email"

        except Exception as e:
            return False, str(e)
