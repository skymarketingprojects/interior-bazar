from rest_framework.response import Response
def ServerResponse(response='', message='', data={}, code=1):
    obj = {
        'response': response,
        'code': code,
        'message': message,
        'data': data,
    }
    return Response(obj)