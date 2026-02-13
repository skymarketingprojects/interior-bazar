from pydantic import BaseModel, Extra

class BaseValidator(BaseModel):
    class Config:
        extra = Extra.ignore
        orm_mode = True

class LocalResponse(BaseValidator):
    response: bool
    code: int
    message: str
    data: dict
