import uuid
from pydantic import BaseModel, Field, EmailStr, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class SkillLevel(str, Enum):
    JUNIOR = "junior"
    MIDDLE = "middle"
    SENIOR = "senior"


class FreelancerStatus(str, Enum):
    pending = "pending"
    approved = "approved"


class Specialization(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    specialization: str
    skill_level: SkillLevel = Field(alias="level")

    @field_validator('skill_level', mode='before')
    @classmethod
    def normalize_skill_level(cls, v):
        if isinstance(v, str):
            return v.lower()
        return v


class FreelancerBase(BaseModel):
    iin: str = Field(..., min_length=12, max_length=12)
    city: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    specializations_with_levels: List[Specialization]


class FreelancerCreate(FreelancerBase):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    surname: Optional[str] = Field(None, min_length=1, max_length=100)
    phone_number: Optional[str] = Field(None, pattern=r'^\+?[1-9]\d{1,14}$')
    payment_info: Optional[Dict[str, Any]] = None
    social_links: Optional[Dict[str, Any]] = None
    portfolio_links: Optional[Dict[str, Any]] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None


class FreelancerUpdate(BaseModel):
    iin: Optional[str] = Field(None, min_length=12, max_length=12)
    city: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    specializations_with_levels: Optional[List[Specialization]] = None
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    surname: Optional[str] = Field(None, min_length=1, max_length=100)
    phone_number: Optional[str] = Field(None, pattern=r'^\+?[1-9]\d{1,14}$')
    payment_info: Optional[Dict[str, Any]] = None
    social_links: Optional[Dict[str, Any]] = None
    portfolio_links: Optional[Dict[str, Any]] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None


class FreelancerResponse(BaseModel):
    freelancer_id: uuid.UUID
    user_id: uuid.UUID
    iin: str
    city: str
    email: str
    specializations_with_levels: List[Specialization]
    name: str
    surname: str
    phone_number: Optional[str]
    status: FreelancerStatus
    payment_info: Dict[str, Any] = Field(default_factory=dict)
    social_links: Dict[str, Any] = Field(default_factory=dict)
    portfolio_links: Dict[str, Any] = Field(default_factory=dict)
    avatar_url: Optional[str]
    bio: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FreelancerApproval(BaseModel):
    status: FreelancerStatus
