from pydantic import BaseModel, Field
from typing import Optional

class Product(BaseModel):
    id_brand: int
    id_category: int
    product_name: str 
    product_image: str
    product_description: str
    id_seller: int
    price: float
    stock: int

class updateProduct(BaseModel):
    id_product: int
    id_brand: int
    id_category: int
    product_name: str 
    product_description: str
    price: float
    stock: int