from asgiref.sync import sync_to_async
from app_ib.models import PlanQuery
from app_ib.Utils.MyMethods import MY_METHODS

class PLAN_TASKS:
    @classmethod
    async def CreatePlanTask(self, payment_proof, user_ins, data):
        try:
            
            plan_query = PlanQuery()
            # plan_query.user= user_ins
            plan_query.plan= data.plan     
            plan_query.name= data.name
            plan_query.email= data.email
            plan_query.phone= data.phone
            plan_query.state= data.state
            plan_query.country= data.country
            # plan_query.address= data.address
            plan_query.stage= "pending"
            plan_query.attachment_url= payment_proof
            plan_query.transaction_id= getattr(data, 'transactionId', '')

            await sync_to_async(plan_query.save)()

            return {"id":plan_query.id}

        except Exception as e:
            #await MY_METHODS.printStatus(f'Error in CreatePlanTask {e}')
            return None


    @classmethod
    async def VerifyPlanTask(self, plan_ins,data):
        try:
            #await MY_METHODS.printStatus(f'Task {plan_ins}')
            plan_ins.stage= 'confirm'
            plan_ins.plan= getattr(data, 'plan', plan_ins.plan)
            plan_ins.name= getattr(data, 'name', plan_ins.name)
            plan_ins.email= getattr(data, 'email', plan_ins.email)
            plan_ins.phone= getattr(data, 'phone', plan_ins.phone)
            plan_ins.state= getattr(data, 'state', plan_ins.state)
            plan_ins.country= getattr(data, 'country', plan_ins.country)
            # plan_query.address= getattr(data, 'address', plan_ins.address)
            plan_ins.stage= getattr(data, 'stage', plan_ins.stage)
            plan_ins.attachment_url= getattr(data, 'attachment_url', plan_ins.attachment_url)
            plan_ins.transaction_id= getattr(data, 'transactionId', plan_ins.transaction_id)
            await sync_to_async(plan_ins.save)()
            return True
            
        except Exception as e:
            #await MY_METHODS.printStatus(f'Error in VerifyPlanTask {e}')
            return None