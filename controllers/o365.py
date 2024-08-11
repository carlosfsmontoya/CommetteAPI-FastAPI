# Importa el módulo para manejar operaciones del sistema, como el acceso a variables de entorno.
import os  

# Importa excepciones y la clase Request de FastAPI.
from fastapi import HTTPException, Request  

# Importa la clase para manejar la autorización OAuth2.
from fastapi.security import OAuth2AuthorizationCodeBearer  

# Importa las respuestas HTTP para redirigir y devolver JSON.
from starlette.responses import RedirectResponse, JSONResponse  

# Importa la clase MSAL para manejar la autenticación con Microsoft.
from msal import ConfidentialClientApplication  

# Importa la función para codificar parámetros de consulta de URL.
from urllib.parse import urlencode  

# Importa el módulo para realizar solicitudes HTTP.
import requests  

# Importa el módulo para generar secretos y tokens seguros.
import secrets  

# Importa el módulo para funciones de hash, como SHA256.
import hashlib  

# Importa el módulo para codificar en base64.
import base64  

# Importa la función para cargar variables de entorno desde un archivo .env.
from dotenv import load_dotenv  

# Carga las variables de entorno desde el archivo .env.
load_dotenv()  

# Obtiene el ID de cliente desde las variables de entorno.
client_id = os.getenv("CLIENT_ID")  

# Obtiene el secreto del cliente desde las variables de entorno.
client_secret = os.getenv("CLIENT_SECRET")  

# Obtiene el ID del inquilino desde las variables de entorno.
tenant_id = os.getenv("TENANT_ID")  

# Obtiene la URI de redirección desde las variables de entorno.
redirect_uri = os.getenv("REDIRECT_URI")  

# Define la URL para solicitar la autorización.
authorization_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/authorize"  

# Define la URL para solicitar el token de acceso.
token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"  

# Configura el esquema de autorización OAuth2 con las URLs correspondientes.
oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=authorization_url,  # URL para la autorización.
    tokenUrl=token_url,  # URL para el intercambio del código por un token.
)

# Crea una instancia de ConfidentialClientApplication para manejar la autenticación.
msal_app = ConfidentialClientApplication(
    client_id,  # ID del cliente para la aplicación.
    authority=f"https://login.microsoftonline.com/{tenant_id}",  # Autoridad de autenticación con el tenant.
    client_credential=client_secret,  # Secreto del cliente para autenticarse.
)

# Diccionario global para almacenar el PKCE verifier asociado con el host.
pkce_verifier_store = {}  

# Función para generar un PKCE verifier seguro.
def generate_pkce_verifier():
    return secrets.token_urlsafe(32)  # Genera un PKCE verifier seguro de 32 bytes y lo devuelve.

# Función para generar un PKCE challenge basado en el PKCE verifier.
def generate_pkce_challenge(verifier):
    digest = hashlib.sha256(verifier.encode()).digest()  # Crea un hash SHA-256 del PKCE verifier.
    return base64.urlsafe_b64encode(digest).rstrip(b'=').decode('ascii')  # Codifica el hash en base64 URL-safe y lo devuelve como una cadena.

# Función asincrónica para iniciar el proceso de inicio de sesión con Office 365.
async def login_o365(request: Request):
    global pkce_verifier_store  # Indica que se usará la variable global pkce_verifier_store.

    pkce_verifier = generate_pkce_verifier()  # Genera un nuevo PKCE verifier.
    pkce_challenge = generate_pkce_challenge(pkce_verifier)  # Genera el PKCE challenge basado en el verifier.

    # Almacena el PKCE verifier asociado con el host del cliente en el diccionario global.
    pkce_verifier_store[request.client.host] = pkce_verifier

    # Define los parámetros para la URL de autorización.
    auth_url_params = {
        "client_id": client_id,  # ID del cliente.
        "response_type": "code",  # Tipo de respuesta esperado: código de autorización.
        "redirect_uri": redirect_uri,  # URI a la que se redirige después de la autorización.
        "response_mode": "query",  # Modo de respuesta: parámetros en la URL.
        "scope": "User.Read",  # Alcance de la solicitud: leer la información del usuario.
        "code_challenge": pkce_challenge,  # Código de desafío PKCE.
        "code_challenge_method": "S256"  # Método de hash usado para el PKCE challenge.
    }
    
    # Construye la URL completa de autorización con los parámetros codificados.
    auth_url = f"{authorization_url}?{urlencode(auth_url_params)}"  
    
    # Redirige al usuario a la URL de autorización.
    return RedirectResponse(auth_url)  

# Función asincrónica para manejar la respuesta del callback de Office 365.
async def auth_callback_o365(request: Request):
    global pkce_verifier_store  # Indica que se usará la variable global pkce_verifier_store.

    # Obtiene el código de autorización de los parámetros de consulta.
    code = request.query_params.get("code")  
    
    # Si el código no está presente en los parámetros de consulta:
    if not code:  
        # Lanza una excepción HTTP 400 indicando que no se encontró el código de autorización.
        raise HTTPException(status_code=400, detail="Authorization code not found")  

    # Recupera el PKCE verifier asociado con el host del cliente.
    pkce_verifier = pkce_verifier_store.get(request.client.host)  
    
    # Si no se encuentra el PKCE verifier:
    if not pkce_verifier:  
        # Lanza una excepción HTTP 400 indicando que no se encontró el PKCE verifier.
        raise HTTPException(status_code=400, detail="PKCE verifier not found")  

    # Define los datos para solicitar el token.
    token_data = {
        "client_id": client_id,  # ID del cliente.
        "client_secret": client_secret,  # Secreto del cliente para autenticarse.
        "grant_type": "authorization_code",  # Tipo de concesión: código de autorización.
        "code": code,  # Código de autorización recibido.
        "redirect_uri": redirect_uri,  # URI de redirección.
        "code_verifier": pkce_verifier  # PKCE verifier para el intercambio.
    }

    # Realiza una solicitud POST para obtener el token.
    token_response = requests.post(token_url, data=token_data)  
    # Convierte la respuesta a formato JSON.
    token_response_data = token_response.json()  

    # Si el token de acceso está presente en los datos de respuesta:
    if "access_token" in token_response_data:  
        # Devuelve el token de acceso en formato JSON.
        return JSONResponse(content={"access_token": token_response_data["access_token"]})  
    else:  
        # Devuelve un error en formato JSON si el token no está presente.
        return JSONResponse(content={
            "error": token_response_data.get("error"),  # Mensaje de error.
            "error_description": token_response_data.get("error_description")  # Descripción del error.
        }, status_code=400)  # Devuelve un estado HTTP 400 en caso de error.
