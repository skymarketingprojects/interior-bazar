from rest_framework.response import Response
from django.conf import settings
def ServerResponse(response:bool, message:str, data={}, code:int=1):
    obj = {
        'response': response,
        'code': code,
        'message': message,
        # 'data': data,
    }
    if settings.DEBUG:
        obj['data'] = data
    else:
        if response:
            obj['data'] = {}
    return Response(obj)