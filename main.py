# Importa el módulo FastAPI y clases para manejo de peticiones y respuestas.
from fastapi import FastAPI, Request, Response  

# Importa el modelo UserRegister desde el módulo models.Userlogin.
from models.Userlogin import UserRegister  

# Importa las funciones para manejar el inicio de sesión y la autenticación de Office 365 desde el módulo controllers.o365.
from controllers.o365 import login_o365, auth_callback_o365  

# Importa el middleware CORS para manejar el intercambio de recursos entre orígenes (CORS).
from fastapi.middleware.cors import CORSMiddleware  

# Importa el decorador para validar JWT desde el módulo utils.security.
from utils.security import validate  

# Crea una instancia de la aplicación FastAPI.
app = FastAPI()  

# Configura el middleware CORS para permitir solicitudes desde cualquier origen y permitir todos los métodos y encabezados.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir todos los orígenes.
    allow_credentials=True,  
    allow_methods=["*"],  # Permitir todos los métodos HTTP.
    allow_headers=["*"],  # Permitir todos los encabezados HTTP.
)

# Define una ruta GET en la raíz de la aplicación que devuelve un mensaje de saludo y la versión de la aplicación.
@app.get("/")  
async def hello():  
    return {
        "Hello": "World",  # Mensaje de saludo.
        "version": "0.1.16"  # Versión de la aplicación.
    }  

# Define una ruta GET para manejar el inicio de sesión, llamando a la función login_o365.
@app.get("/login")  
async def login(request: Request):  
    return await login_o365(request)  

# Define una ruta GET para manejar la autenticación de Office 365, llamando a la función auth_callback_o365.
@app.get("/auth/callback")  
async def authcallback(request: Request):  
    return await auth_callback_o365(request)  

# Define una ruta GET protegida que devuelve el email del usuario si el JWT es válido.
@app.get("/user")  
@validate  # Aplica el decorador para validar el JWT antes de ejecutar la función.
async def user(request: Request):  
    return {
        "email": request.state.email  # Devuelve el email del usuario desde el estado de la solicitud.
    }  

# Ejecuta la aplicación FastAPI usando uvicorn si el script se ejecuta directamente.
if __name__ == "__main__":  
    import uvicorn  # Importa el servidor ASGI uvicorn.
    uvicorn.run(app, host="0.0.0.0", port=8000)  # Ejecuta la aplicación en el host 0.0.0.0 y puerto 8000.
