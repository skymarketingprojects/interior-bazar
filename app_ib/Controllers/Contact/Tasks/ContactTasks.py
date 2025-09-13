from asgiref.sync import sync_to_async
from app_ib.models import Contact
from app_ib.Utils.MyMethods import MY_METHODS
class CONTACT_TASKS:
    
    @classmethod
    async def CreateContactTask(self,data):
        try:
            # await MY_METHODS.printStatus(f'create contact task data {data}')
            contact_ins= await sync_to_async(Contact.objects.create)(
                tag=data.tag,
                name = data.name,
                phone = data.phone,
                mail = data.mail,
                company = data.company,
                recognisation = data.recognisation,
                detail = data.detail,
                attachment = getattr(data, 'attachment', None)
            )
            await MY_METHODS.printStatus(f'contact ins {contact_ins}')

            if contact_ins:
                return True
            else:
                return False

        except Exception as e:
            await MY_METHODS.printStatus(f'create contact task error {str(e)}')
            return False