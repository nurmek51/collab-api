import uuid
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ClientBase(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    surname: Optional[str] = Field(None, min_length=1, max_length=100)
    phone_number: Optional[str] = Field(None, pattern=r'^\+?[1-9]\d{1,14}$')


class ClientCreate(ClientBase):
    pass


class ClientUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    surname: Optional[str] = Field(None, min_length=1, max_length=100)
    phone_number: Optional[str] = Field(None, pattern=r'^\+?[1-9]\d{1,14}$')


class ClientResponse(BaseModel):
    client_id: uuid.UUID
    user_id: uuid.UUID
    name: Optional[str]
    surname: Optional[str]
    phone_number: Optional[str]
    company_ids: List[uuid.UUID] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
