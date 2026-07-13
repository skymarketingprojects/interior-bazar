from rest_framework.response import Response
def ServerResponse(response:bool, message:str, data=None, code:int=1):
    # Envelope shape is a contract with the frontends (ApiResponseType<T>):
    # data must ALWAYS be present — previously it was stripped to {} (success)
    # or omitted entirely (error) whenever DEBUG=False, silently breaking prod.
    return Response({
        'response': response,
        'code': code,
        'message': message,
        'data': {} if data is None else data,
    })
