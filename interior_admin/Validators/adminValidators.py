from rbac_module.Controllers.AccessController.AccessController import ACCESS_CONTROLLER
from django.core.exceptions import PermissionDenied
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.models import CustomUser
from rbac_module.models import Access, Role
from rest_framework.request import Request
from app_ib.Utils.BaseValidator import BaseValidator
from typing import List, Optional

def get_permission_name(request: Request):
    resolver = request.resolver_match
    app_label = resolver.app_name or "default"
    url_name = resolver.url_name
    method = request.method.lower()
    return f"{app_label}:{url_name}:{method}"

async def hasAccess(user=None, accessName: str = None, request: Request = None):
    """
    Checks if a user has access to a specific permission.
    Supports dynamic permission derivation from the request object.
    Automatically creates missing Access entries.
    Bypasses checks for roles with is_full_access=True.
    """
    # 1. Determine User
    if not user and request:
        user = request.user
    
    if not user:
        raise PermissionDenied(RESPONSE_MESSAGES.unauthorized)

    # 2. Universal Access Check (Django superuser or is_full_access role)
    if getattr(user, "is_superuser", False):
        return True
    if await Role.objects.filter(users=user, is_full_access=True).aexists():
        return True

    # 3. Derive access name if not provided (Dynamic mode)
    if not accessName and request:
        accessName = get_permission_name(request)

    if not accessName:
        # Fallback to Admin check if no permission name can be determined
        isAdmin = await IsAdmin(user)
        if not isAdmin:
            raise PermissionDenied(RESPONSE_MESSAGES.unauthorized)
        return True

    # 4. Auto-Register new permissions if they don't exist
    await Access.objects.aget_or_create(
        permissionName=accessName,
        defaults={'permission': True}
    )

    # 5. Standard RBAC check
    accessResp = await ACCESS_CONTROLLER.checkUserHasAccess(user, accessName)
    if not accessResp.data:
        raise PermissionDenied(RESPONSE_MESSAGES.unauthorized)

    return True

async def IsAdmin(user:CustomUser):
    if user.type == 'admin':
        return True
    return False

class CreateAdminUser(BaseValidator):
    username: str
    password: str
    name: str
    email: str
    phone: str
    roles: List[int]

class UpdateAdminUser(BaseValidator):
    username: Optional[str]
    password: Optional[str]
    name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    roles: Optional[List[int]]