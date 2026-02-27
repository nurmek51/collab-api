from pydantic import BaseModel, Field
from typing import Optional


class OTPRequest(BaseModel):
    phone_number: str = Field(
        ...,
        pattern=r'^\+?[1-9]\d{1,14}$',
        description="Phone number in E.164 format. Example: +1234567890"
    )


class OTPVerification(BaseModel):
    phone_number: str = Field(
        ...,
        pattern=r'^\+?[1-9]\d{1,14}$',
        description="Phone number in E.164 format. Must match OTP destination."
    )
    code: str = Field(..., min_length=4, max_length=6, description="OTP code from SMS/WhatsApp")
    firebase_token: Optional[str] = Field(
        default=None,
        description="Optional Firebase ID token. Used only on /auth/verify-otp for alternative verification path. Not used by /auth/request-otp."
    )


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_expires_in: int


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., min_length=20, description="Refresh token received from /auth/verify-otp")


class RoleSelection(BaseModel):
    role: str = Field(..., pattern=r'^(client|freelancer|admin)$')
