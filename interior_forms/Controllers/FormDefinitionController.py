"""
Read layer for public form definitions. Raises NotFound_ for unknown or
inactive keys so the exceptionHandler decorator maps it to code 410
(RESPONSE_CODES.not_exist) — same contract as the engine controllers.
"""
from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Controllers.Engine.CrudController import NotFound_
from interior_forms.models import FormDefinition


class FORM_DEFINITION_CONTROLLER:

    @staticmethod
    def getDefinition(key: str):
        definition = FormDefinition.objects.filter(key=key, is_active=True).first()
        if definition is None:
            raise NotFound_("form definition not found")

        return LocalResponse(
            response=RESPONSE_MESSAGES.success,
            code=RESPONSE_CODES.success,
            message=RESPONSE_MESSAGES.form_definition_fetch_success,
            data={
                'key': definition.key,
                'version': definition.version,
                'schema': definition.schema,
            },
        )
