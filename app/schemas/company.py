import uuid
from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime


class CompanyBase(BaseModel):
    company_industry: Optional[str] = Field(None, max_length=100)
    client_position: Optional[str] = Field(None, max_length=100)
    company_name: Optional[str] = Field(None, max_length=200)
    company_size: Optional[int] = Field(None, ge=1)
    company_logo: Optional[str] = Field(None, max_length=500)
    company_description: Optional[str] = None


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(CompanyBase):
    pass


class CompanyResponse(CompanyBase):
    company_id: uuid.UUID
    client_id: uuid.UUID
    owner_ids: List[uuid.UUID] = Field(default_factory=list)
    company_orders: List[uuid.UUID] = Field(default_factory=list)
    orders: List[Any] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
