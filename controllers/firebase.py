import os
import requests
import json
import logging
import traceback
import random

from dotenv import load_dotenv
from fastapi import HTTPException, Depends

from azure.storage.queue import QueueClient, BinaryBase64DecodePolicy, BinaryBase64EncodePolicy

import firebase_admin
from firebase_admin import credentials, auth as firebase_auth
from utils.database import fetch_query_as_json, get_db_connection
from utils.security import create_jwt_token
from models.UserRegister import UserRegister
from models.UserLogin import UserLogin
from models.UserActivation import UserActivation

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Inicializar la app de Firebase Admin
cred = credentials.Certificate("secrets/commette-sdk.json")
firebase_admin.initialize_app(cred)

load_dotenv()

azure_sak = os.getenv('AZURE_SAK')
queue_name = os.getenv('QUEUE_ACTIVATE')
go_endpoint = os.getenv("GO_ENDPOINT")
x_secret_key = os.getenv("X_SECRET_KEY")
headers = {
    "X-Secret-Key": x_secret_key,
    "Content-Type": "application/json"
}
queue_client = QueueClient.from_connection_string(azure_sak, queue_name)
queue_client.message_decode_policy = BinaryBase64DecodePolicy()
queue_client.message_encode_policy = BinaryBase64EncodePolicy()

async def inser_message_on_queue(message: str):
    message_bytes = message.encode('utf-8')
    print(message_bytes)
    queue_client.send_message(
        queue_client.message_encode_policy.encode(message_bytes)
    )


async def register_user_firebase(user: UserRegister):
    print(user)
    try:
        # Verificar si el username ya existe
        if await check_exists('commette.[User]', 'username', user.username):
            raise HTTPException(status_code=400, detail="El nombre de usuario ya está en uso.")
        
        # Si es vendedor, verificar si el nombre de la empresa ya existe
        if user.companyName and await check_exists('commette.[Seller]', 'company_name', user.companyName):
            raise HTTPException(status_code=400, detail="El nombre de la empresa ya está en uso.")
        
        # Crear usuario en Firebase Authentication
        user_record = firebase_auth.create_user(
            email=user.email,
            password=user.password
        )

        await inser_message_on_queue(user.email)

        # Insertar usuario en la base de datos 
        conn = await get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                DECLARE @new_user_id INT;
                EXEC commette.create_user 
                    @username = ?, 
                    @firstname = ?, 
                    @lastname = ?, 
                    @email = ?, 
                    @is_seller = ?, 
                    @company_name = ?;
                SELECT @new_user_id;
                """,
                user.username,
                user.firstname,
                user.lastname,
                user.email,
                1 if user.companyName else 0,  # 1 si es vendedor, 0 si no
                user.companyName if user.companyName else None
            )

            # Obtener el ID del usuario recién insertado
            user_id = cursor.fetchone()[0]

            # Enviar el ID del usuario al endpoint de Go
            data = {
                "id_user": user_id
            }
            response = requests.post(go_endpoint, headers=headers, json=data)
            if response.status_code != 201:
                raise HTTPException(status_code=response.status_code, detail=response.text)

            conn.commit()
            return {
                "success": True,
                "message": "Usuario registrado exitosamente"
            }
        
            
        except Exception as e:
            print(e)
            # Eliminar el usuario en Firebase si hay un error al insertar en la base de datos
            if 'user_record' in locals():
                firebase_auth.delete_user(user_record.uid)
            conn.rollback()
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            cursor.close()
            conn.close()

    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=400,
            detail=f"Error al registrar usuario: {e}"
        )

async def login_user_firebase(user: UserLogin):
    try:
        # Autenticar usuario con Firebase Authentication usando la API REST
        api_key = os.getenv("FIREBASE_API_KEY") 
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"
        payload = {
            "email": user.email,
            "password": user.password,
            "returnSecureToken": True
        }
        response = requests.post(url, json=payload)
        response_data = response.json()

        if "error" in response_data:
            raise HTTPException(
                status_code=400,
                detail=f"Error al autenticar usuario: {response_data['error']['message']}"
            )

        query = f"""select 
                        id_user
                        , email
                        , first_name
                        , last_name
                        , role
                        , active
                    from [commette].[User]
                    where email = '{ user.email }'
                    """

        try:
            result_json = await fetch_query_as_json(query)
            result_dict = json.loads(result_json)
            return {
                "message": "Usuario autenticado exitosamente",
                "idToken": create_jwt_token(
                    result_dict[0]["id_user"],
                    result_dict[0]["first_name"],
                    result_dict[0]["last_name"],
                    user.email,
                    result_dict[0]["role"],
                    result_dict[0]["active"]
                )
            }
        except Exception as e:
            print(e)
            raise HTTPException(status_code=500, detail=str(e))


    except Exception as e:
        error_detail = {
            "type": type(e).__name__,
            "message": str(e),
            "traceback": traceback.format_exc()
        }
        raise HTTPException(
            status_code=400,
            detail=f"Error al registrar usuario: {error_detail}"
        )
 
    
async def generate_activation_code(email: str):

    code = random.randint(100000, 999999)
    query = f" exec commette.generate_activation_code @email = '{email}', @code = {code}"
    result = {}
    try:
        result_json = await fetch_query_as_json(query, is_procedure=True)
        result = json.loads(result_json)[0]

    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "message": "Código de activación generado exitosamente",
        "code": code
    }


async def check_exists(table: str, column: str, value: str) -> bool:
    conn = await get_db_connection()
    cursor = conn.cursor()
    try:
        query = f"SELECT COUNT(*) FROM {table} WHERE {column} = ?"
        cursor.execute(query, (value,))
        exists = cursor.fetchone()[0] > 0
        return exists
    finally:
        cursor.close()
        conn.close()


async def activate_user(user: UserActivation):
    query = f"""
            select 
                email 
                , case
                    when GETDATE() between created_at and expired_at then 'active'
                    else 'expired'
                end as status
            from [commette].[activation_codes] 
            where code = {user.code}
            and email = '{user.email}';
            """

    try:
        result_json = await fetch_query_as_json(query)
        result_dict = json.loads(result_json)
        if len(result_dict) == 0:
            raise HTTPException(status_code=404, detail="Código de activación no encontrado")

        if result_dict[0]["status"] == "expired":
            await inser_message_on_queue(user.email)
            raise HTTPException(status_code=400, detail="Código de activación expirado")

        query = f"""
                exec commette.activate_user @email = '{user.email}';
                """
        result_json = await fetch_query_as_json(query, is_procedure=True)

        return {
            "message": "Usuario activado exitosamente"
        }
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))