import enum
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Table, Numeric, DateTime, Enum, CheckConstraint, func
from sqlalchemy.orm import relationship
from .database import Base

role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", Integer, ForeignKey(
        "roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", Integer, ForeignKey(
        "permissions.id", ondelete="CASCADE"), primary_key=True),
)


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)

    users = relationship("User", back_populates="role")
    permissions = relationship(
        "Permission", secondary=role_permissions, back_populates="roles")


class Permission(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, nullable=False)

    roles = relationship("Role", secondary=role_permissions,
                         back_populates="permissions")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True,)
    email = Column(String, index=True, nullable=False)
    password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)

    role = relationship("Role", back_populates="users")
    products = relationship("Product", back_populates="owner")
    bids = relationship("Bid", back_populates="bidder")


class ProductStatus(str, enum.Enum):
    draft = "draft"
    open = "open"
    ended = "ended"
    sold = "sold"
    closed = "closed"


class Product(Base):
    __tablename__ = "product"
    __table_args__ = (CheckConstraint(
        "start_price >= 0", name="ck_start_price_nonneg"),)

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    title = Column(String(255), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    start_price = Column(Numeric(12, 2), nullable=False)
    current_price = Column(Numeric(12, 2), nullable=False)
    the_number_of_auction = Column(Integer, nullable=False, default=0)
    status = Column(Enum(ProductStatus), nullable=False,
                    default=ProductStatus.draft)
    end_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(),
                        onupdate=func.now())

    owner = relationship("User", back_populates="products")
    bids = relationship("Bid", back_populates="product",cascade="all,delete-orphan")
    accepted_bid_count_id = Column(Integer, nullable=True)

    @property
    def owner_name(self):
        return self.owner.name


class BidStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"


class Bid(Base):
    __tablename__ = "bids"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey(
        "product.id"), nullable=False, index=True)
    bidder_id = Column(Integer, ForeignKey(
        "users.id"), nullable=False, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    status = Column(Enum(BidStatus), nullable=False, default=BidStatus.pending)
    created_at = Column(DateTime, server_default=func.now())

    product = relationship("Product", back_populates="bids")
    bidder = relationship("User", back_populates="bids")

    @property
    def bidder_name(self):
        return self.bidder.name

    @property
    def product_title(self):
        return self.product.title
