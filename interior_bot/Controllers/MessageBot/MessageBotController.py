from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.LocalResponse import LocalResponse
from interior_bot.models import MessageBot

from .Tasks.MessageBotTasks import MESSAGE_BOT_TASKS
from app_ib.Utils.Names import NAMES

from django.core.cache import cache

class MESSAGE_BOT_CONTROLLER:
    
    @classmethod
    async def GetMessages(self):
        try:
            cache_key = "bot_messages_all"
            cached_data = cache.get(cache_key)
            if cached_data:
                return LocalResponse(
                    response=RESPONSE_MESSAGES.success,
                    code=RESPONSE_CODES.success,
                    data=cached_data,
                    message="messages found (cached)"
                )

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
            
            # Cache for 24 hours
            cache.set(cache_key, messageData, 86400)

            return LocalResponse(
                response=RESPONSE_MESSAGES.success,
                code=RESPONSE_CODES.success,
                data=messageData,
                message="messages found"
            )
        except Exception as e:
            pass
            return LocalResponse(
                response=RESPONSE_MESSAGES.error,
                code=RESPONSE_CODES.error,
                data={NAMES.ERROR:str(e)},
                message="messages found Error"
            )


