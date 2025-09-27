from asgiref.sync import sync_to_async


class ADMIN_LEADS_VALIDATORS:
    
    @classmethod
    async def IsAdmin(self,user):
        if user.type == 'admin':
            return True
        return False
