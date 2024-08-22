from pydantic import BaseModel, validator
from typing import Optional
import re

from utils.globalf import validate_sql_injection

class UserRegister(BaseModel):
    email: str
    password: str
    firstname: str
    lastname: str
    username: str  # Añadido para incluir el nombre de usuario
    companyName: Optional[str] = None  # Opcional para incluir el nombre de la empresa si es necesario

    @validator('password')
    def password_validation(cls, value):
        if len(value) < 6:
            raise ValueError('Password must be at least 6 characters long')

        if not re.search(r'[A-Z]', value):
            raise ValueError('Password must contain at least one uppercase letter')

        if not re.search(r'[\W_]', value):  # \W matches any non-word character
            raise ValueError('Password must contain at least one special character')

        if re.search(r'(012|123|234|345|456|567|678|789|890)', value):
            raise ValueError('Password must not contain a sequence of numbers')

        return value

    @validator('firstname', 'lastname')
    def name_validation(cls, value):
        if validate_sql_injection(value):
            raise ValueError('Invalid name')

        return value

    @validator('email')
    def email_validation(cls, value):
        if not re.match(r"[^@]+@[^@]+\.[^@]+", value):
            raise ValueError('Invalid email address')

        return value

    @validator('username')
    def username_validation(cls, value):
        if validate_sql_injection(value):
            raise ValueError('Invalid username')
        
        if len(value) < 3:
            raise ValueError('Username must be at least 3 characters long')

        if not re.match(r'^[a-zA-Z0-9_]+$', value):
            raise ValueError('Username can only contain alphanumeric characters and underscores')

        return value

    @validator('companyName', always=True)
    def company_name_validation(cls, value, values):
        if values.get('is_seller') and not value:
            raise ValueError('Company name must be provided for sellers')
        return value
