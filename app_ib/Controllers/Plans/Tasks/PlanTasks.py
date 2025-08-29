from asgiref.sync import sync_to_async
from app_ib.models import PlanQuery

class PLAN_TASKS:
    @classmethod
    async def CreatePlanTask(self, payment_proof, user_ins, data):
        try:
            
            plan_query = PlanQuery()
            plan_query.user= user_ins
            plan_query.plan= data.plan     
            plan_query.name= data.name
            plan_query.email= data.email
            plan_query.phone= data.phone
            plan_query.state= data.state
            plan_query.country= data.country
            plan_query.address= data.address
            plan_query.stage= "pending"

            # # If transaction id had and attachment is None
            if(not data.transaction_id and not payment_proof):
                print(f'Both are None')
                plan_query.stage= "pending"

                await sync_to_async(plan_query.save)()
                return False

            # # If transaction id or attachment both are None 
            if(data.transaction_id and payment_proof):
                # Test: 
                print(f'BOTH EXIST')
                print(f'payment_proof  {payment_proof}')
                print(f'transaction id {data.transaction_id}')

                plan_query.stage= "complete"
                plan_query.transaction_id= data.transaction_id
                plan_query.attachment= payment_proof
                
                await sync_to_async(plan_query.save)()
                return True
            
            
            # Any one exist 
            if(data.transaction_id or payment_proof):
                print(f'Any one exist')
                if(data.transaction_id):
                    print(f'transaction id {data.transaction_id}')
                    plan_query.transaction_id= data.transaction_id

                if(payment_proof):
                    print(f'payment_proof  {payment_proof}')
                    plan_query.transaction_id= data.transaction_id

                await sync_to_async(plan_query.save)()
                return True

        except Exception as e:
            print(f'Error in CreatePlanTask {e}')
            return None


    @classmethod
    async def VerifyPlanTask(self, plan_ins):
        try:
            print(f'Task {plan_ins}')
            plan_ins.stage= 'confirm'
            await sync_to_async(plan_ins.save)()
            return True
            
        except Exception as e:
            print(f'Error in VerifyPlanTask {e}')
            return None