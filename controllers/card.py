import json
import logging

from dotenv import load_dotenv
from fastapi import HTTPException, Depends
from utils.database import fetch_query_as_json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def execute_query(query: str):
    try:
        logger.info(f"EXECUTING QUERY: {query}")
        result_json = await fetch_query_as_json(query)
        result_dict = json.loads(result_json)
        return result_dict
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def fetch_cards(email: str):
    query = f"""
        select
            id,
            title,
            description,
            u.firstname + ' ' + u.lastname as author,
            cast(c.created_at as nvarchar(100)) as created_at,
            cast(c.updated_at as nvarchar(100)) as updated_at,
            case
                when c.email = '{email}' THEN 'Mine'
                else 'Shared'
            end as access
        from otd.cards c
        inner join otd.users u
        on c.email = u.email
        order by updated_at desc
    """

    try:
        logger.info(f"QUERY LIST")
        result_json = await fetch_query_as_json(query)
        result_dict = json.loads(result_json)
        return result_dict
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def fetch_card(id: int, email: str):
    query = f"""
        select
            id
            , title
            , description
        from otd.cards
        where id = {id}
        and email = '{email}'
    """
    result_dict = []
    try:
        logger.info(f"QUERY LIST")
        result_json = await fetch_query_as_json(query)
        result_dict = json.loads(result_json)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if len(result_dict) == 0:
            raise HTTPException(status_code=404, detail="Card not found")

    return result_dict[0]

async def delete_card(id: int, email: str):
    query = f"EXEC otd.delete_card @email='{email}' ,@card_id = {id};"
    result = {}
    try:

        logger.info(f"QUERY DELETE")
        result_json = await fetch_query_as_json(query, is_procedure=True)
        result = json.loads(result_json)[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if result["status"] == 404:
        raise HTTPException(status_code=404, detail="Card not found")

    return result

async def fetch_update_card(id: int, title: str, description: str):
    query = f"EXEC otd.update_card @id = {id}, @title = '{title}', @description = '{description}';"
    result = {}
    try:

        logger.info(f"QUERY UPDATE")
        result_json = await fetch_query_as_json(query, is_procedure=True)
        result = json.loads(result_json)[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if result["status"] == 404:
        raise HTTPException(status_code=404, detail="Card not found")

    return result


async def fetch_create_card(email:str, title: str, description: str):
    query = f"EXEC otd.create_card @email='{email}',  @title = '{title}', @description = '{description}';"
    result = {}
    try:

        logger.info(f"QUERY UPDATE")
        result_json = await fetch_query_as_json(query, is_procedure=True)
        result = json.loads(result_json)[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if result["status"] == 404:
        raise HTTPException(status_code=404, detail="Card not found")

    return result