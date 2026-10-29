from typing import List, Optional
from pydantic import BaseModel


class Owner(BaseModel):
    owner_name: str
    owner_email: str
    owner_password: str


class Shwo_Owner(BaseModel):
    owner_id: int
    owner_name: str
    owner_email: str
    owner_password: str

    class Config:
        from_attributes = True


class custamer(BaseModel):
    custamer_id: int
    custamer_name: str
    custamer_email: str
    custamer_password: str


class Shwo_custamer(BaseModel):
    custamer_id: int
    custamer_name: str
    custamer_email: str
    custamer_password: str


class product(BaseModel):
    product_id: int
    product_title: str


class Show_product(BaseModel):
    product_id: int
    product_title: str
