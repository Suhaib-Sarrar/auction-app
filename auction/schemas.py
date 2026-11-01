from typing import List, Optional
from pydantic import BaseModel


class Owner(BaseModel):
    owner_name: str
    owner_email: str
    owner_password: str


class Show_Owner(BaseModel):
    owner_id: int
    owner_name: str
    owner_email: str
    owner_password: str

    class Config:
        from_attributes = True


class Customer(BaseModel):
    customer_id: int
    customer_name: str
    customer_email: str
    customer_password: str


class Show_customer(BaseModel):
    customer_id: int
    customer_name: str
    customer_email: str
    customer_password: str

    class Config:
        from_attributes = True


class product(BaseModel):
    product_id: int
    product_title: str


class Show_product(BaseModel):
    product_id: int
    product_title: str
