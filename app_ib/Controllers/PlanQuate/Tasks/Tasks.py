from asgiref.sync import sync_to_async
from app_ib.models import Quate
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.Utils.Names import NAMES


class PLAN_QUATE_TASKS:
    @classmethod
    async def CreateQuateTask(cls, data):
        try:
            quate_ins = Quate()

            # Only set attributes that are both in the model and provided in data
            model_fields = [field.name for field in Quate._meta.get_fields() if field.editable and field.name != NAMES.ID]

            for field in model_fields:
                value = getattr(data, field, None)
                if value is not None:
                    setattr(quate_ins, field, value)

            await sync_to_async(quate_ins.save)()
            #await MY_METHODS.printStatus(f'quate instance pk {quate_ins.pk}')
            return quate_ins.pk

        except Exception as e:
            #await MY_METHODS.printStatus(f'Error in CreatePlanQuateTask {e}')
            return None



    @classmethod
    async def VerifyQuateTask(cls, quate_ins, data):
        try:
            model_fields = [field.name for field in Quate._meta.get_fields() if field.editable and field.name != NAMES.ID]

            for field in model_fields:
                new_value = getattr(data, field, None)
                if new_value is not None:
                    setattr(quate_ins, field, new_value)
                # else: retain the old value (which is already in quate_ins)

            await sync_to_async(quate_ins.save)()
            return True

        except Exception as e:
            #await MY_METHODS.printStatus(f'Error in VerifyQuateTask {e}')
            return None