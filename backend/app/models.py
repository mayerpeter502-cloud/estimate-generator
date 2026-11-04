from sqlalchemy import Column, String, Float, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.database import Base  # <-- ИМПОРТИРУЕМ Base ОТСЮДА

def generate_uuid():
    return str(uuid.uuid4())


class Business(Base):
    __tablename__ = "businesses"
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=True)


class Category(Base):
    __tablename__ = "categories"
    id = Column(String, primary_key=True, default=generate_uuid)
    business_id = Column(String, ForeignKey("businesses.id"), nullable=False)
    name = Column(String, nullable=False)
    
    # Обратное отношение
    items = relationship("ServiceItem", order_by="ServiceItem.id", back_populates="category")


class ServiceItem(Base):
    __tablename__ = "service_items"
    id = Column(String, primary_key=True, default=generate_uuid)
    category_id = Column(String, ForeignKey("categories.id"), nullable=False)
    name = Column(String, nullable=False)
    base_price = Column(Float, nullable=False)
    unit = Column(String, default="услуга")
    description = Column(Text, nullable=True)
    metadata_ = Column("metadata", Text, default="{}")
    
    # Отношение к категории
    category = relationship("Category", back_populates="items")


class Estimate(Base):
    __tablename__ = "estimates"
    id = Column(String, primary_key=True, default=generate_uuid)
    business_id = Column(String, ForeignKey("businesses.id"), nullable=False)
    client_name = Column(String, nullable=False)
    client_phone = Column(String, nullable=True)
    work_object = Column(String, nullable=True, default="")
    items_data = Column(Text, nullable=False)
    total = Column(Float, nullable=False)
    status = Column(String, default="created")
    created_at = Column(DateTime(timezone=True), server_default=func.now())