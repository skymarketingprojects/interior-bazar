from asgiref.sync import sync_to_async
from interior_bot.models import MessageBot
from app_ib.Utils.MyMethods import MY_METHODS
class MESSAGE_BOT_TASKS:
    
    @classmethod
    async def GetMessageQuestionTask(self,bot:MessageBot):
        try:
            botData = {
                "question":bot.question,
                "link":bot.link
            }
            return botData
        except Exception as e:
            await MY_METHODS.printStatus(f"Error getting message data : {str(e)}")
            return False

