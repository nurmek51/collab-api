from pydantic import BaseModel, Field
from typing import Optional


class OTPRequest(BaseModel):
    phone_number: str = Field(..., pattern=r'^\+?[1-9]\d{1,14}$')


class OTPVerification(BaseModel):
    phone_number: str = Field(..., pattern=r'^\+?[1-9]\d{1,14}$')
    code: str = Field(..., min_length=4, max_length=6)
    firebase_token: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class RoleSelection(BaseModel):
    role: str = Field(..., pattern=r'^(client|freelancer|admin)$')
