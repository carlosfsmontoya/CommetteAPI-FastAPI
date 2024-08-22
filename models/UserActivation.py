from pydantic import BaseModel, validator
from typing import Optional
import re

from utils.globalf import validate_sql_injection

class UserActivation(BaseModel):
    email: str
    code: int

    @validator('email')
    def email_validation(cls, value):
        if not re.match(r"[^@]+@[^@]+\.[^@]+", value):
            raise ValueError('Invalid email address')

        return value