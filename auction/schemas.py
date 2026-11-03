from typing import Literal, Optional
from pydantic import BaseModel, Field, ConfigDict, field_serializer
from datetime import datetime
from decimal import Decimal
from .models import ProductStatus


class User(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: str
    password: str = Field(min_length=8, max_length=50)
    role: Literal["owner", "customer"]


class Show_user(BaseModel):
    name: str
    email: str


class User_owner(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class Product(BaseModel):

    name: str
    title: str
    start_price: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    end_time: datetime | None = None
    status: Literal["draft", "open"] = "draft"


class ProductUpdate(BaseModel):
    name: str | None = None
    title: str | None = None
    start_price: Decimal | None = Field(
        default=None, ge=0, max_digits=12, decimal_places=2)
    end_time: datetime | None = None
    status: Literal["draft", "open"] | None = None


class Show_Product(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    owner_name: str
    id: int
    name: str
    title: str
    current_price: Decimal
    the_number_of_auction: int
    end_time: datetime | None
    status: ProductStatus

    @field_serializer("end_time")
    def format_end_time(self, value: datetime | None):
        return value.strftime("%Y-%m-%d %I:%M %p") if value else None


class Show_Product_Owner(Show_Product):
    start_price: Decimal


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    name: str | None = None
