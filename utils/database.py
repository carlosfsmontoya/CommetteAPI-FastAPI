from dotenv import load_dotenv
import os
import pymssql
import logging
import json

from decimal import Decimal

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

server = os.getenv('SQL_SERVER')
database = os.getenv('SQL_DATABASE')
username = os.getenv('SQL_USERNAME')
password = os.getenv('SQL_PASSWORD')

# pymssql no requiere un controlador ODBC, así que la cadena de conexión es más simple
connection_string = {
    'server': server,
    'user': username,
    'password': password,
    'database': database
}

async def get_db_connection():
    try:
        logger.info(f"Intentando conectar a la base de datos en el servidor: {server}")
        conn = pymssql.connect(**connection_string)
        logger.info("Conexión exitosa a la base de datos.")
        return conn
    except pymssql.Error as e:
        logger.error(f"Database connection error: {str(e)}")
        raise Exception(f"Database connection error: {str(e)}")

async def fetch_query_as_json(query, is_procedure=False):
    conn = await get_db_connection()
    cursor = conn.cursor()
    logger.info(f"Ejecutando query: {query}")
    try:
        cursor.execute(query)

        if is_procedure and cursor.description is None:
            conn.commit()
            return json.dumps([{"status": 200, "message": "Procedure executed successfully"}])

        columns = [column[0] for column in cursor.description]
        results = []
        logger.info(f"Columns: {columns}")
        for row in cursor.fetchall():
            row_dict = dict(zip(columns, row))
            results.append(decimal_to_float(row_dict))

        return json.dumps(results)

    except pymssql.Error as e:
        raise Exception(f"Error ejecutando el query: {str(e)}")
    finally:
        cursor.close()
        conn.close()

def decimal_to_float(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: decimal_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [decimal_to_float(i) for i in obj]
    else:
        return obj