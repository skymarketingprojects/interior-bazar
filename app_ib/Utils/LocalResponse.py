import dotsi
def LocalResponse(response='', message='', data={}, code=1):
    obj = {
        'response': response,
        'code': code,
        'message': message,
        'data': data,
    }
    model = dotsi.Dict(obj)
    return model