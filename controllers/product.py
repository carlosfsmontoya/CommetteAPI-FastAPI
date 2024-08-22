import json
import logging
from fastapi import HTTPException
from utils.database import fetch_query_as_json
from models.Product import Product, updateProduct

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def execute_query(query: str):
    try:
        logger.info(f"EXECUTING QUERY: {query}")
        result = {}
        
        result_json = await fetch_query_as_json(query, is_procedure=True)
        result = json.loads(result_json)[0]
        logger.info(f"QUERY RESULT: {result_json}")
        
        if result_json is None:
            raise HTTPException(status_code=500, detail="Query returned no result")
        
        result_dict = json.loads(result_json)
        return result_dict
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")



async def fetch_categories():
    query = """
        SELECT
            id_category AS id,
            category_name AS name,
            category_description AS description
        FROM [commette].[Category]
        ORDER BY id_category
    """
    try:
        logger.info(f"QUERY FETCH CATEGORIES")
        result_json = await fetch_query_as_json(query)
        result_dict = json.loads(result_json)
        return result_dict
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def fetch_brands():
    query = """
        SELECT
            id_brand AS id,
            brand_name AS name,
            brand_description AS description
        FROM [commette].[Brand]
        ORDER BY id_brand
    """
    try:
        logger.info(f"QUERY FETCH BRANDS")
        result_json = await fetch_query_as_json(query)
        result_dict = json.loads(result_json)
        return result_dict
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def create_product(product: Product):
    query = f"""
        EXEC commette.create_product
            @id_brand = {product.id_brand},
            @id_category = {product.id_category},
            @product_name = '{product.product_name}',
            @product_image = '{product.product_image or ''}',
            @product_description = '{product.product_description or ''}',
            @id_user = {product.id_seller},
            @price = {product.price},
            @stock = {product.stock}
    """
    try:
        logger.info(f"QUERY CREATE PRODUCT: {query}")
        result_dict = await execute_query(query)
        logger.info(f"RESULT CREATE PRODUCT: {result_dict}")
        if result_dict is None:
            raise HTTPException(status_code=500, detail="No result returned from create product")
        return result_dict
    except Exception as e:
        logger.error(f"Error creating product: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

async def fetch_product_info():
    query = "EXEC commette.product_info"
    try:
        logger.info(f"QUERY FETCH PRODUCT INFO: {query}")
        result_json = await fetch_query_as_json(query, is_procedure=False)
        
        if result_json is None:
            raise HTTPException(status_code=500, detail="No result returned from fetch product info")
        
        result_dict = json.loads(result_json)
        logger.info(f"RESULT FETCH PRODUCT INFO: {result_dict}")
        return result_dict
    except Exception as e:
        logger.error(f"Error fetching product info: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

async def update_product(product: updateProduct):
    query = f"""
        EXEC commette.update_product
            @id_product = {product.id_product},
            @id_brand = {product.id_brand},
            @id_category = {product.id_category},
            @product_name = '{product.product_name}',
            @product_description = '{product.product_description or ''}',
            @price = {product.price},
            @stock = {product.stock}
    """
    try:
        logger.info(f"QUERY UPDATE PRODUCT: {query}")
        result_dict = await execute_query(query)
        logger.info(f"RESULT UPDATE PRODUCT: {result_dict}")
        if result_dict is None:
            raise HTTPException(status_code=500, detail="No result returned from update product")
        return result_dict
    except Exception as e:
        logger.error(f"Error updating product: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
