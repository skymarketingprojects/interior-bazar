from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.LocalResponse import LocalResponse
from interior_bot.models import MessageBot

from .Tasks.MessageBotTasks import MESSAGE_BOT_TASKS
from app_ib.Utils.Names import NAMES

class MESSAGE_BOT_CONTROLLER:
    
    @classmethod
    async def GetMessages(self):
        try:
            messages = MessageBot.objects.all()
            if not messages:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.error,
                    code=RESPONSE_CODES.error,
                    message="no questions exit",
                    data={}
                )
            
            messageData = []
            for message in messages:
                data = await MESSAGE_BOT_TASKS.GetMessageQuestionTask(message)
                messageData.append(data)
            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                code=RESPONSE_CODES.success,
                data=messageData,
                message="messages found"
            )
        except Exception as e:
            # await MY_METHODS.printStatus(f"Error fetching enum: {str(e)}")
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                code=RESPONSE_CODES.error,
                data={NAMES.ERROR:str(e)},
                message="messages found Error"
            )


