from asgiref.sync import sync_to_async
from app_ib.models import Feedback

class FEEDBACK_TASKS:
    @classmethod
    async def CreateFeedbackTask(self,user_ins, data):
        try:
            feedback_ins = Feedback()
            feedback_ins.user= user_ins
            feedback_ins.contact= data.contact
            feedback_ins.feedback= data.feedback     
            await sync_to_async(feedback_ins.save)()
            return True
            
        except Exception as e:
            print(f'Error in CreateFeedback {e}')
            return None

    @classmethod
    async def UdpateFeedbackTask(self,feedback_ins, data):
        try:
            feedback_ins.status= data.status 
            await sync_to_async(feedback_ins.save)()
            return True
            
        except Exception as e:
            print(f'Error in UdpateFeedbackTask {e}')
            return None