from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from asgiref.sync import sync_to_async

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    @sync_to_async
    def get_token(cls, user):
        token = super().get_token(user)
    
        generatedToken = {
            'refresh':str(token),
            'access':str(token.access_token)
        }
        return generatedToken