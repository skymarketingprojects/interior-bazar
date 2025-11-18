from asgiref.sync import sync_to_async
from app_ib.models import CustomUser

class ADMIN_LEADS_VALIDATORS:
    
    @classmethod
    async def IsAdmin(self,user:CustomUser):
        if user.type == 'admin':
            return True
        return False
