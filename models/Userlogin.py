# Importa la clase BaseModel y el decorador validator de Pydantic para la validación de datos.
from pydantic import BaseModel, validator  

# Importa la clase Optional para campos opcionales en los modelos de datos.
from typing import Optional  

# Importa el módulo re para trabajar con expresiones regulares.
import re  

# Importa la función validate_sql_injection desde un módulo local.
from utils.globalf import validate_sql_injection  

# Define un modelo de datos para el registro de usuarios.
class UserRegister(BaseModel):  
    # Define el campo 'email' como una cadena obligatoria.
    email: str  
    
    # Define el campo 'password' como una cadena obligatoria.
    password: str  
    
    # Define el campo 'name' como una cadena opcional.
    name: Optional[str]  

    # Valida el campo 'password' utilizando un decorador de clase.
    @validator('password')  
    def password_validation(cls, value):  
        # Verifica si la longitud de la contraseña es menor que 6 caracteres.
        if len(value) < 6:  
            # Lanza una excepción si la contraseña es demasiado corta.
            raise ValueError('Password must be at least 6 characters long')  

        # Verifica si la contraseña contiene al menos una letra mayúscula.
        if not re.search(r'[A-Z]', value):  
            # Lanza una excepción si falta una letra mayúscula.
            raise ValueError('Password must contain at least one uppercase letter')  

        # Verifica si la contraseña contiene al menos un carácter especial.
        if not re.search(r'[\W_]', value):  # \W coincide con cualquier carácter no alfanumérico
            # Lanza una excepción si falta un carácter especial.
            raise ValueError('Password must contain at least one special character')  

        # Verifica si la contraseña contiene una secuencia de números prohibida.
        if re.search(r'(012|123|234|345|456|567|678|789|890)', value):  
            # Lanza una excepción si se encuentra una secuencia de números prohibida.
            raise ValueError('Password must not contain a sequence of numbers')  

        # Devuelve el valor de la contraseña si pasa todas las validaciones.
        return value  

    # Valida el campo 'name' utilizando un decorador de clase.
    @validator('name')  
    def name_validation(cls, value):  
        # Verifica si el nombre contiene inyecciones SQL usando una función externa.
        if validate_sql_injection(value):  
            # Lanza una excepción si se detecta una posible inyección SQL.
            raise ValueError('Invalid name')  

        # Devuelve el valor del nombre si pasa la validación.
        return value  
