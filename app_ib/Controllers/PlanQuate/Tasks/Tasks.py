from asgiref.sync import sync_to_async
from app_ib.models import Quate

class PLAN_QUATE_TASKS:
    @classmethod
    async def CreateQuateTask(self, data):
        try:
            quate_ins = Quate()
            quate_ins.phone= data.phone
            quate_ins.interested= data.interested     
            quate_ins.email= data.email
            quate_ins.note= data.note
            await sync_to_async(quate_ins.save)()
            print(f'quate instance pk {quate_ins.pk}')
            return quate_ins.pk
            
        except Exception as e:
            print(f'Error in CreatePlanQuateTask {e}')
            return None


    @classmethod
    async def VerifyQuateTask(self, quate_ins, data):
        try:
            quate_ins.phone= data.phone
            quate_ins.interested= data.interested     
            quate_ins.email= data.email
            quate_ins.note= data.note
            await sync_to_async(quate_ins.save)()
            # print(f'quate instance pk {quate_ins.pk}')
            return True
            
        except Exception as e:
            print(f'Error in VerifyQuateTask {e}')
            return None