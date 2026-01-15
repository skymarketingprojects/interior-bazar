from pydantic import BaseModel, Extra

class BaseValidator(BaseModel):
    class Config:
        extra = Extra.ignore
        orm_mode = True
