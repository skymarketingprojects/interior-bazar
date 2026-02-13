import dotsi
def LocalResponse(response:bool=True, message:str='', data={}, code:int=1):
    obj = {
        'response': response,
        'code': code,
        'message': message,
        'data': data,
    }
    model = dotsi.Dict(obj)
    return model