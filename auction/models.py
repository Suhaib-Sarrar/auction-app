from sqlalchemy import Column, Integer, String, ForeignKey
from .database import Base
from sqlalchemy.orm import relationship


class Owner(Base):
    __tablename__ = "Owner"

    owner_id = Column(Integer, primary_key=True, index=True)
    owner_name = Column(String)
    owner_email = Column(String)
    owner_password = Column(String)


class Customer(Base):
    __tablename__ = "Custamer"
    customer_id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String)
    customer_email = Column(String)
    customer_password = Column(String)


class Product(Base):
    __tablename__ = "Product"
    product_id = Column(Integer, primary_key=True, index=True)
    product_title = Column(String)

