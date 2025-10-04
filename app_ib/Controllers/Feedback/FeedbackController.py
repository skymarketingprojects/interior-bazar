from asgiref.sync import sync_to_async
from adrf.decorators import api_view
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.LocalResponse import LocalResponse
from app_ib.models import Feedback
from app_ib.Controllers.Feedback.Tasks.FeedbackTasks import FEEDBACK_TASKS


class FEEDBACK_CONTROLLER:
    @classmethod
    async def CreateFeedback(self,user_ins,data):
        try:
            # Test Data
            # #await MY_METHODS.printStatus(f'name: {data.contact}')
            # #await MY_METHODS.printStatus(f'name: {data.feedback}')

            feedback_create_resp_data = await FEEDBACK_TASKS.CreateFeedbackTask(user_ins=user_ins,data=data)
            #await MY_METHODS.printStatus(f'create query resp {feedback_create_resp_data}')

            if feedback_create_resp_data:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.success,
                    message=RESPONSE_MESSAGES.feedback_generate_success,
                    code=RESPONSE_CODES.success,
                    data={})

            else:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.feedback_generate_error,
                    code=RESPONSE_CODES.error,
                    data={})

        except Exception as e:
            #await MY_METHODS.printStatus(f'Error in CreateFeedback: {e}')
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.feedback_generate_error,
                code=RESPONSE_CODES.error,
                data={
                    'error': str(e)
                })


    @classmethod
    async def UpdateFeedbackStatus(self,data):
        try:
            # Test Data
            # #await MY_METHODS.printStatus(f'id: {data.id}')
            # #await MY_METHODS.printStatus(f'status: {data.status}')

            is_feedback_exist= await sync_to_async(Feedback.objects.filter(id=data.id).exists)()
            if(is_feedback_exist):
                feedback_ins=await sync_to_async(Feedback.objects.get)(id=data.id)
                #await MY_METHODS.printStatus(f'feedback ins {feedback_ins}')

                udpdate_feedback_response = await  FEEDBACK_TASKS.UdpateFeedbackTask(feedback_ins=feedback_ins, data=data)
                #await MY_METHODS.printStatus(f'udpate feedback resp {udpdate_feedback_response}')

                if udpdate_feedback_response:
                    return LocalResponse(
                        response=RESPONSE_MESSAGES.success,
                        message=RESPONSE_MESSAGES.feedback_update_success,
                        code=RESPONSE_CODES.success,
                        data={})

                else:
                    return LocalResponse(
                        response=RESPONSE_MESSAGES.error,
                        message=RESPONSE_MESSAGES.feedback_update_error,
                        code=RESPONSE_CODES.error,
                        data={})
            else:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.feedback_update_error,
                    code=RESPONSE_CODES.error,
                    data={})

        except Exception as e:
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                message=RESPONSE_MESSAGES.feedback_update_error,
                code=RESPONSE_CODES.error,
                data={
                    'error': str(e)
                })