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
def create_jwt_token(email: str, active: bool):  
    # Define la fecha y hora de expiración del token, que es 1 hora desde la creación.
    expiration = datetime.utcnow() + timedelta(hours=1)  
    # Codifica el payload del token con la clave secreta usando el algoritmo HS256.
    token = jwt.encode(
        {
            "email": email,  # Incluye el email del usuario en el payload.
            "exp": expiration,  # Incluye la fecha de expiración del token en el payload.
            "active": active,  # Incluye el estado de actividad del usuario en el payload.
            "iat": datetime.utcnow()  # Incluye la fecha y hora de emisión del token.
        },
        SECRET_KEY,  # Usa la clave secreta para firmar el token.
        algorithm="HS256"  # Especifica el algoritmo de firma.
    )  
    # Devuelve el token codificado.
    return token  

# Define un decorador para validar un JWT en las peticiones.
def validate(func):  
    # Define una función interna para validar el JWT y ejecutar la función original.
    @wraps(func)  
    async def wrapper(*args, **kwargs):  
        # Obtiene el objeto request de los argumentos de la función.
        request = kwargs.get('request')  
        if not request:  
            # Lanza una excepción si no se encuentra el objeto request.
            raise HTTPException(status_code=400, detail="Request object not found")  

        # Obtiene el encabezado de autorización de la petición.
        authorization: str = request.headers.get("Authorization")  
        if not authorization:  
            # Lanza una excepción si el encabezado de autorización está ausente.
            raise HTTPException(status_code=403, detail="Authorization header missing")  

        try:  
            # Divide el encabezado de autorización en esquema y token.
            scheme, token = authorization.split()  
            if scheme.lower() != "bearer":  
                # Lanza una excepción si el esquema de autorización no es Bearer.
                raise HTTPException(status_code=403, detail="Invalid authentication scheme")  

            # Decodifica el token usando la clave secreta y el algoritmo HS256.
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])  

            # Obtiene los datos del payload del token.
            email = payload.get("email")  
            expired = payload.get("exp")  
            active = payload.get("active")  
            if email is None or expired is None or active is None:  
                # Lanza una excepción si faltan datos en el payload.
                raise HTTPException(status_code=403, detail="Invalid token")  

            if datetime.utcfromtimestamp(expired) < datetime.utcnow():  
                # Lanza una excepción si el token ha expirado.
                raise HTTPException(status_code=403, detail="Expired token")  

            if not active:  
                # Lanza una excepción si el usuario está inactivo.
                raise HTTPException(status_code=403, detail="Inactive user")  

            # Inyecta el email del usuario en el objeto request para su uso posterior.
            request.state.email = email  
        except PyJWTError:  
            # Lanza una excepción si ocurre un error al decodificar el token.
            raise HTTPException(status_code=403, detail="Invalid token or expired token")  

        # Llama a la función original con los argumentos dados.
        return await func(*args, **kwargs)  
    return wrapper  # Devuelve el decorador.
