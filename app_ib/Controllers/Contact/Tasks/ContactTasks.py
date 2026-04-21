from asgiref.sync import sync_to_async
from app_ib.models import Contact
from app_ib.Utils.MyMethods import MY_METHODS
from app_ib.Utils.Names import NAMES
class CONTACT_TASKS:
    
    @classmethod
    async def CreateContactTask(self,data):
        try:
            pass
            contact_ins= await sync_to_async(Contact.objects.create)(
                tag=data.tag,
                name = data.name,
                phone = data.phone,
                mail = data.mail,
                company = data.company,
                recognisation = data.recognisation,
                detail = data.detail,
                attachment = getattr(data, NAMES.ATTACHMENT, None)
            )
            pass

            if contact_ins:
                return True
            else:
                return False

        except Exception as e:
            pass
            return False