from asgiref.sync import sync_to_async
from typing import Any, Dict, Tuple

from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.decorators.ViewDecorator import controllerExceptionHandler
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES

from interior_admin.models import NotificationTemplate
from .Validators.TemplatesValidators import TemplateCreateSchema, TemplateUpdateSchema


def _tmpl_dict(t: NotificationTemplate) -> Dict[str, Any]:
    return {
        "id": t.id, "key": t.key, "channel": t.channel, "subject": t.subject,
        "body": t.body, "variables": t.variables or [], "active": t.active,
        "updatedAt": t.updatedAt.isoformat() if t.updatedAt else "",
    }


class TemplatesController:

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def List(cls) -> Tuple[bool, Dict[str, Any]]:
        rows = await sync_to_async(list)(NotificationTemplate.objects.all())
        return True, {"templates": [_tmpl_dict(t) for t in rows]}

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def Create(cls, payload: TemplateCreateSchema) -> Tuple[bool, Dict[str, Any]]:
        if await NotificationTemplate.objects.filter(key=payload.key).aexists():
            return False, {"message": f"Template key '{payload.key}' already exists"}
        t = await NotificationTemplate.objects.acreate(
            key=payload.key, channel=payload.channel or 'email',
            subject=payload.subject or '', body=payload.body or '',
            variables=payload.variables or [], active=payload.active if payload.active is not None else True)
        return True, _tmpl_dict(t)

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def Update(cls, templateId: int, payload: TemplateUpdateSchema) -> Tuple[bool, Dict[str, Any]]:
        t = await NotificationTemplate.objects.filter(id=templateId).afirst()
        if t is None:
            return False, {"message": "Template not found"}
        for field in ("channel", "subject", "body", "variables", "active"):
            val = getattr(payload, field)
            if val is not None:
                setattr(t, field, val)
        await sync_to_async(t.save)()
        return True, _tmpl_dict(t)

    @classmethod
    @controllerExceptionHandler(errorMessage=RESPONSE_MESSAGES.default_error, responseFunc=LocalResponse)
    async def Delete(cls, templateId: int) -> Tuple[bool, Dict[str, Any]]:
        t = await NotificationTemplate.objects.filter(id=templateId).afirst()
        if t is None:
            return False, {"message": "Template not found"}
        await sync_to_async(t.delete)()
        return True, {"id": templateId, "deleted": True}


TEMPLATES_CONTROLLER = TemplatesController()
