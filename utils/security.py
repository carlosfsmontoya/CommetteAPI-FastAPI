# Importa módulos para manejo de entorno, generación de tokens, y manejo de fechas.
import os  
import secrets  
import hashlib  
import base64  
import jwt  

from datetime import datetime, timedelta  # Importa clases para manejo de fechas y tiempos.
from fastapi import HTTPException  # Importa clase para manejar excepciones HTTP en FastAPI.
from dotenv import load_dotenv  # Importa función para cargar variables de entorno desde un archivo .env.
from jwt import PyJWTError  # Importa clase para manejar errores específicos de JWT.
from functools import wraps  # Importa decorador para funciones.

# Carga las variables de entorno desde el archivo .env.
load_dotenv()  

# Obtiene la clave secreta desde las variables de entorno.
SECRET_KEY = os.getenv("SECRET_KEY")  
SECRET_KEY_FUNC = os.getenv("SECRET_KEY_FUNC")

# Define una función para generar un PKCE verifier utilizando tokens seguros.
def generate_pkce_verifier():  
    # Devuelve un token URL-safe de 32 bytes para ser usado como PKCE verifier.
    return secrets.token_urlsafe(32)  

# Define una función para generar un PKCE challenge a partir de un PKCE verifier.
def generate_pkce_challenge(verifier):  
    # Calcula el hash SHA-256 del PKCE verifier.
    digest = hashlib.sha256(verifier.encode()).digest()  
    # Codifica el hash en base64 URL-safe y elimina los caracteres de relleno.
    return base64.urlsafe_b64encode(digest).rstrip(b'=').decode('ascii')  

# Define una función para crear un JWT (JSON Web Token).
def create_jwt_token(id_user: int, firstname: str, lastname: str, email: str, role: str, active: bool):
    expiration = datetime.utcnow() + timedelta(hours=1)  # El token expira en 1 hora
    token = jwt.encode(
        {
            "id_user": id_user,
            "firstname": firstname,
            "lastname": lastname,
            "email": email,
            "role": role,
            "active": active,
            "exp": expiration,
            "iat": datetime.utcnow()
        },
        SECRET_KEY,
        algorithm="HS256"
    )
    return token

# Define un decorador para validar un JWT en las peticiones.
def validate(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        request = kwargs.get('request')
        if not request:
            raise HTTPException(status_code=400, detail="Request object not found")

        authorization: str = request.headers.get("Authorization")
        if not authorization:
            raise HTTPException(status_code=400, detail="Authorization header missing")

        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=400, detail="Invalid authentication scheme")

        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])

            id_user = payload.get("id_user")
            email = payload.get("email")
            expired = payload.get("exp")
            active = payload.get("active")
            firstname = payload.get("firstname")
            lastname = payload.get("lastname")
            role = payload.get("role")

            if id_user is None or email is None or expired is None or active is None or role is None:
                raise HTTPException(status_code=400, detail="Invalid token")

            if datetime.utcfromtimestamp(expired) < datetime.utcnow():
                raise HTTPException(status_code=401, detail="Expired token")

            if not active:
                raise HTTPException(status_code=403, detail="Inactive user")

            # Inyectar los valores en el objeto request
            request.state.id_user = id_user
            request.state.email = email
            request.state.firstname = firstname
            request.state.lastname = lastname
            request.state.role = role
        except PyJWTError:
            raise HTTPException(status_code=401, detail="Invalid token or expired token")

        return await func(*args, **kwargs)
    return wrapper


def validate_for_inactive(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        request = kwargs.get('request')
        if not request:
            raise HTTPException(status_code=400, detail="Request object not found")

        authorization: str = request.headers.get("Authorization")
        if not authorization:
            raise HTTPException(status_code=400, detail="Authorization header missing")

        try:
            scheme, token = authorization.split()
            if scheme.lower() != "bearer":
                raise HTTPException(status_code=400, detail="Invalid authentication scheme")

            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])

            email = payload.get("email")
            expired = payload.get("exp")

            if email is None or expired is None:
                raise HTTPException(status_code=400, detail="Invalid token")

            if datetime.utcfromtimestamp(expired) < datetime.utcnow():
                raise HTTPException(status_code=401, detail="Expired token")



            # Inyectar el email en el objeto request
            request.state.email = email
        except PyJWTError:
            raise HTTPException(status_code=403, detail="Invalid token or expired token")

        return await func(*args, **kwargs)
    return wrapper

def validate_func(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        request = kwargs.get('request')
        if not request:
            raise HTTPException(status_code=400, detail="Request object not found")

        authorization: str = request.headers.get("Authorization")
        if not authorization:
            raise HTTPException(status_code=403, detail="Authorization header missing")

        if authorization != SECRET_KEY_FUNC:
            raise HTTPException(status_code=403, detail="Wrong function key")

        return await func(*args, **kwargs)
    return wrapper