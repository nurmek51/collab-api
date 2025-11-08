import uuid
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum


class ApplicationStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class OrderApplicationBase(BaseModel):
    order_id: uuid.UUID
    freelancer_id: uuid.UUID


class OrderApplicationCreate(OrderApplicationBase):
    vacancy_id: Optional[uuid.UUID] = None  # ID of the specific vacancy/specialization being applied to


class OrderApplicationUpdate(BaseModel):
    status: ApplicationStatus


class OrderApplicationResponse(OrderApplicationBase):
    id: uuid.UUID
    company_id: uuid.UUID
    status: ApplicationStatus
    specialization_index: Optional[int] = None
    specialization_name: Optional[str] = None
    vacancy_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
