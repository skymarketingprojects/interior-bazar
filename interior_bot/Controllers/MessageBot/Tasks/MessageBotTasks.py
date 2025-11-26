from asgiref.sync import sync_to_async
from interior_bot.models import MessageBot
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.Utils.Names import NAMES
class MESSAGE_BOT_TASKS:
    
    @classmethod
    async def GetMessageQuestionTask(self,bot:MessageBot):
        try:
            botData = {
                NAMES.QUESTION:bot.question,
                NAMES.LINK:bot.link
            }
            return botData
        except Exception as e:
            # await MY_METHODS.printStatus(f'Error getting message data : {str(e)}')
            return False

