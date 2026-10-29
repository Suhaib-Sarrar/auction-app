from sqlalchemy import Column, Integer, String, ForeignKey
from .database import Base
from sqlalchemy.orm import relationship


class Owner(Base):
    __tablename__ = "Owner"

    owner_id = Column(Integer, primary_key=True, index=True)
    owner_name = Column(String)
    owner_email = Column(String)
    owner_password = Column(String)


class custamer(Base):
    __tablename__ = "Custamer"
    custamer_id = Column(Integer, primary_key=True, index=True)
    custamer_name = Column(String)
    custamer_email = Column(String)
    custamer_password = Column(String)


class product(Base):
    __tablename__ = "Product"
    product_id = Column(Integer, primary_key=True, index=True)
    product_title = Column(String)
    pass
