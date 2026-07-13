import inspect
import asyncio
from functools import wraps
from typing import Callable

from django.core.exceptions import ValidationError, ObjectDoesNotExist,PermissionDenied
from django.db import IntegrityError
from app_ib.Utils.ResponseCodes import RESPONSE_CODES
from app_ib.Utils.ResponseMessages import RESPONSE_MESSAGES
from app_ib.Utils.MyMethods import MY_METHODS
# Engine controllers signal not-found / ownership / conflict with these custom
# exceptions (plain Exception subclasses, not Django's). Handling them here keeps
# the codes identical to the old EngineGapsView _err wrapper (task 19). Safe import:
# CrudController pulls only django.db + EngineConfig, never ViewDecorator.
from app_ib.Controllers.Engine.CrudController import NotFound_, PermissionError_, Conflict_

def exceptionHandler(
    *,
    errorMessage: str="",
    successMessage: str="",
    viewResponse:bool = True,
    responseFunc: Callable = None,
):
    """
    Universal decorator for async/sync views, controllers, services.
    """

    def decorator(func: Callable):

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                if inspect.isawaitable(result):
                    result = await result
                
                pass
                if viewResponse:

                    return responseFunc(
                        response = result.response,
                        message = result.message,
                        code = result.code,
                        data = result.data
                    )
                status,data = result
                
                if status:
                    return responseFunc(
                        response = RESPONSE_MESSAGES.success,
                        message = successMessage,
                        code = RESPONSE_CODES.success,
                        data = data
                    )
                else:
                    return responseFunc(
                        response = RESPONSE_MESSAGES.error,
                        message = errorMessage,
                        code = RESPONSE_CODES.error,
                        data = data
                    )
            
            except asyncio.CancelledError:
                raise

            # engine controller signals — preserve _err codes (task 19)
            except NotFound_ as e:
                return responseFunc(
                    response=RESPONSE_MESSAGES.error,
                    message=str(e),
                    code=RESPONSE_CODES.not_exist,
                    data={},
                )

            except PermissionError_ as e:
                return responseFunc(
                    response=RESPONSE_MESSAGES.error,
                    message=str(e),
                    code=RESPONSE_CODES.forbidden,
                    data={},
                )

            except Conflict_ as e:
                return responseFunc(
                    response=RESPONSE_MESSAGES.error,
                    message=str(e),
                    code=RESPONSE_CODES.conflict,
                    data={},
                )

            except PermissionDenied as e:
                pass
                return responseFunc(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.permission_denied,
                    code=RESPONSE_CODES.forbidden,
                    data={},
                )
            # ✅ validation / bad input
            except ValidationError as e:
                pass
                return responseFunc(
                    response=RESPONSE_MESSAGES.error,
                    message=str(e),
                    code=RESPONSE_CODES.validation_error,
                    data={},
                )

            # ✅ uniqueness / constraint conflicts
            except IntegrityError as e:
                pass
                return responseFunc(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.resource_already_exists,
                    code=RESPONSE_CODES.conflict,
                    data={},
                )

            # ✅ logical not found
            except ObjectDoesNotExist as e:
                pass
                return responseFunc(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.resource_not_found,
                    code=RESPONSE_CODES.not_found,
                    data={},
                )

            # ✅ permission / ownership issues
            except PermissionError as e:
                pass
                return responseFunc(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.permission_denied,
                    code=RESPONSE_CODES.forbidden,
                    data={},
                )

            # ✅ bad input / state
            except (ValueError, TypeError, KeyError) as e:
                pass
                return responseFunc(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.bad_request,
                    code=RESPONSE_CODES.bad_request,
                    data={},
                )

            # ❌ everything else (internal)
            except Exception as e:
                pass

                return responseFunc(
                    response=RESPONSE_MESSAGES.error,
                    message=errorMessage,
                    code=RESPONSE_CODES.error,
                    data={},
                )

        if inspect.iscoroutinefunction(func):
            return async_wrapper

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)

            # engine controller signals — preserve _err codes (task 19)
            except NotFound_ as e:
                return responseFunc(
                    response=RESPONSE_MESSAGES.error,
                    message=str(e),
                    code=RESPONSE_CODES.not_exist,
                    data={},
                )

            except PermissionError_ as e:
                return responseFunc(
                    response=RESPONSE_MESSAGES.error,
                    message=str(e),
                    code=RESPONSE_CODES.forbidden,
                    data={},
                )

            except Conflict_ as e:
                return responseFunc(
                    response=RESPONSE_MESSAGES.error,
                    message=str(e),
                    code=RESPONSE_CODES.conflict,
                    data={},
                )

            except ValidationError as e:
                return responseFunc(
                    response=RESPONSE_MESSAGES.error,
                    message=str(e),
                    code=RESPONSE_CODES.validation_error,
                    data={},
                )

            except IntegrityError as e:

                return responseFunc(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.resource_already_exists,
                    code=RESPONSE_CODES.conflict,
                    data={},
                )

            except ObjectDoesNotExist:
                return responseFunc(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.resource_not_found,
                    code=RESPONSE_CODES.not_found,
                    data={},
                )

            except PermissionError:
                return responseFunc(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.permission_denied,
                    code=RESPONSE_CODES.forbidden,
                    data={},
                )

            except (ValueError, TypeError, KeyError) as e:
                return responseFunc(
                    response=RESPONSE_MESSAGES.error,
                    message=RESPONSE_MESSAGES.bad_request,
                    code=RESPONSE_CODES.bad_request,
                    data={},
                )

            except Exception:

                return responseFunc(
                    response=RESPONSE_MESSAGES.error,
                    message=errorMessage,
                    code=RESPONSE_CODES.error,
                    data={},
                )

        return sync_wrapper

    return decorator

def controllerExceptionHandler(
    *,
    errorMessage: str = "",
    successMessage: str = "",
    responseFunc: Callable = None,
):
    """
    Wrapper for exceptionHandler with viewResponse=False by default.
    Use this for controllers/services where you want
    success responses to use the result as data.
    """
    return exceptionHandler(
        errorMessage=errorMessage,
        successMessage=successMessage,
        responseFunc=responseFunc,
        viewResponse=False  # <— always False for controllers
    )


def taskExceptionHandler(func):

    if inspect.iscoroutinefunction(func):

        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)

            except asyncio.CancelledError:
                raise   # ← never convert to (False, msg)

            except Exception as e:
                return False, str(e)

        return wrapper

    else:

        @wraps(func)
        def wrapper_sync(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                return False, str(e)

        return wrapper_sync
