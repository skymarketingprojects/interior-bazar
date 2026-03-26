from app_ib.Utils.BaseValidator import BaseValidator
from typing import Optional, List, Literal
from datetime import datetime
from pydantic import Field, EmailStr, validator

class UpdatePlanIntent(BaseValidator):
    buyIntent: Optional[str]
    planId: Optional[int]