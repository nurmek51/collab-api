import uuid
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class UserBase(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    surname: Optional[str] = Field(None, min_length=1, max_length=100)
    phone_number: str = Field(..., pattern=r'^\+?[1-9]\d{1,14}$')


class UserCreate(UserBase):
    roles: List[str] = Field(default_factory=list)


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    surname: Optional[str] = Field(None, min_length=1, max_length=100)
    phone_number: Optional[str] = Field(None, pattern=r'^\+?[1-9]\d{1,14}$')


class UserResponse(BaseModel):
    user_id: uuid.UUID
    name: Optional[str]
    surname: Optional[str]
    phone_number: Optional[str]
    roles: List[str]
    has_avatar: bool = False
    avatar_uploaded_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AvatarUploadResponse(BaseModel):
    has_avatar: bool = True
    avatar_uploaded_at: datetime


class AvatarDownloadResponse(BaseModel):
    download_url: str
    expires_in_seconds: int
