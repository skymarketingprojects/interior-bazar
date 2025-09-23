from asgiref.sync import sync_to_async
from app_ib.models import UserProfile
from app_ib.Utils.MyMethods import MY_METHODS

class PROFILE_TASKS:
    @classmethod
    async def CreateProfileTask(self, user_ins, data):
        try:
            user_profile_ins = UserProfile()
            user_profile_ins.user = user_ins
            user_profile_ins.name = data.name
            user_profile_ins.email = data.email
            user_profile_ins.phone = data.phone
            user_profile_ins.profile_image_url = data.profile_image_url
            await sync_to_async(user_profile_ins.save)()
            return True
            
        except Exception as e:
            await MY_METHODS.printStatus(f'Error in CreateProfileTask {e}')
            return None

    @classmethod
    async def UpdateProfileTask(self, user_profile_ins, data):
        try:
            user_profile_ins.name = data.name
            user_profile_ins.email = data.email
            user_profile_ins.phone = data.phone
            user_profile_ins.profile_image_url = data.profile_image_url
            await sync_to_async(user_profile_ins.save)()
            return True
            
        except Exception as e:
            await MY_METHODS.printStatus(f'Error in UpdateProfileTask {e}')
            return None

    @classmethod
    async def CreateProfileImageTask(self, user_ins, profile_image):
        try:
            user_profile_ins = UserProfile()
            user_profile_ins.user = user_ins
            user_profile_ins.profile_image_url = profile_image
            await sync_to_async(user_profile_ins.save)()
            return True
            
        except Exception as e:
            await MY_METHODS.printStatus(f'Error in CreateProfileImageTask {e}')
            return None

    @classmethod
    async def UpdateProfileImageTask(self, user_profile_ins, profile_image):
        try:
            user_profile_ins.profile_image = profile_image
            await sync_to_async(user_profile_ins.save)()
            return True
            
        except Exception as e:
            await MY_METHODS.printStatus(f'Error in UpdateProfileImageTask {e}')
            return None


    @classmethod
    async def GetProfileDataTask(self, user_profile_ins):
        try:
            user_profile_data = {
                "profile_image_url": user_profile_ins.profile_image_url if user_profile_ins.profile_image_url else '',
                'name': user_profile_ins.name if user_profile_ins.name else '',
                'email': user_profile_ins.email if user_profile_ins.email else '',
                'phone': user_profile_ins.phone if user_profile_ins.phone else '',
            }
            if(user_profile_ins.profile_image):
                user_profile_data['profile_image']=user_profile_ins.profile_image.url
            return user_profile_data
            
        except Exception as e:
            await MY_METHODS.printStatus(f'Error in GetProfileDataTask {e}')
            return None