from pydantic import BaseModel
from typing import Optional, List


class BusinessCreate(BaseModel):
    name: str
    phone: Optional[str] = None


class CategoryCreate(BaseModel):
    name: str


class ServiceItemCreate(BaseModel):
    name: str
    base_price: float
    unit: str = "услуга"
    description: Optional[str] = None
    metadata_: Optional[dict] = None


class EstimateItem(BaseModel):
    item_id: str
    quantity: int = 1


class EstimateCreate(BaseModel):
    client_name: str
    client_phone: Optional[str] = None
    work_object: Optional[str] = ""  # ← НОВОЕ ПОЛЕ
    items: List[EstimateItem]