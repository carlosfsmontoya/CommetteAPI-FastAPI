# Importa el módulo FastAPI y clases para manejo de peticiones y respuestas.
from fastapi import FastAPI, Request, Response  

# Importa el modelo UserRegister desde el módulo models.Userlogin.
from models.UserRegister import UserRegister
from models.UserLogin import UserLogin
from models.UserActivation import UserActivation
from models.Product import Product, updateProduct
# Importa las funciones para manejar el inicio de sesión y la autenticación de Office 365 desde el módulo controllers.o365.
from controllers.o365 import login_o365, auth_callback_o365  
from controllers.google import login_google , auth_callback_google
from controllers.firebase import register_user_firebase, login_user_firebase, generate_activation_code, activate_user
from controllers.product import execute_query, fetch_categories, fetch_brands, create_product, fetch_product_info, update_product
# Importa el middleware CORS para manejar el intercambio de recursos entre orígenes (CORS).
from fastapi.middleware.cors import CORSMiddleware  
from fastapi import Request

# Importa el decorador para validar JWT desde el módulo utils.security.
from utils.security import validate, validate_func, validate_for_inactive

import logging
from fastapi import HTTPException
logger = logging.getLogger("uvicorn")

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
        "Hello": "World",  
        "version": "0.1.16"  
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
@validate
async def user(request: Request, response: Response):
    state_dict = vars(request.state)
    print(state_dict)
    response.headers["Cache-Control"] = "no-cache"
    return {
        "id_user": request.state.id_user,
        "email": request.state.email,
        "firstname": request.state.firstname,
        "lastname": request.state.lastname,
        "role": request.state.role
    }


@app.get("/login/google")
async def logingoogle():
    return await login_google()

@app.get("/auth/google/callback")
async def authcallbackgoogle(request: Request):
    return await auth_callback_google(request)


@app.post("/register")
async def register(user: UserRegister):
    return await register_user_firebase(user)

@app.post("/login/custom")
async def login_custom(user: UserLogin):
    return await login_user_firebase(user)

@app.get("/cards")
async def cards(request: Request, response: Response):
    response.headers["Cache-Control"] = "no-cache"
    return await execute_query("SELECT * FROM [commette].[cards]")

@app.post("/user/{email}/code")
@validate_func
async def generate_code(request: Request, email: str):
    return await generate_activation_code(email)


@app.put("/user/code/{code}")
@validate_for_inactive
async def generate_code(request: Request, code: int):
    user = UserActivation(email=request.state.email, code=code)
    return await activate_user(user)

@app.get("/categories")
@validate
async def get_categories(request: Request, response: Response):
    response.headers["Cache-Control"] = "no-cache"
    return await fetch_categories()

@app.get("/brands")
@validate
async def get_brands(request: Request, response: Response):
    response.headers["Cache-Control"] = "no-cache"
    return await fetch_brands()



@app.post("/product")
@validate
async def add_product(request: Request, response: Response, product: Product):
    response.headers["Cache-Control"] = "no-cache"
    return await create_product(product)

@app.get("/products")
@validate
async def get_products(request: Request, response: Response):
    return await fetch_product_info()


@app.get("/products/{product_id}")
@validate
async def get_products_by_user_id(request: Request, response: Response, product_id: int):
    query = f"EXEC commette.get_product_by_id @ProductID = {product_id}"
    result = await execute_query(query)
    return result


@app.get("/products/user/{user_id}")
@validate
async def get_products_by_user_id(request: Request, response: Response, user_id: int):
    query = f"EXEC commette.get_products_by_user_id @UserID = {user_id}"
    result = await execute_query(query)
    return result

@app.delete("/product/{product_id}")
@validate
async def delete_product_by_id(request: Request, response: Response, product_id: int):
    try:
        query = f"EXEC commette.delete_product_and_inventory @id_product = {product_id}"
        result = await execute_query(query)
        if result is None:
            response.status_code = 404
            return {"detail": "Product not found"}
        return {"detail": "Product and associated inventory deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/product/{product_id}")
@validate
async def update_product_endpoint(request: Request, response: Response, product_id: int, product: updateProduct):
    print(product)
    try:
        result = await update_product(product)
        return result
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


# Ejecuta la aplicación FastAPI usando uvicorn si el script se ejecuta directamente.
if __name__ == "__main__":  
    import uvicorn  # Importa el servidor ASGI uvicorn.
    uvicorn.run(app, host="0.0.0.0", port=8000)  # Ejecuta la aplicación en el host 0.0.0.0 y puerto 8000.
