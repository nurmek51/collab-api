from typing import Optional
import structlog

from ..repositories.user import UserRepository
from ..config.auth import verify_otp, create_access_token
from ..config.firebase import verify_firebase_token
from ..schemas.auth import OTPVerification, TokenResponse
from ..exceptions import BadRequestException

logger = structlog.get_logger()


class AuthService:
    def __init__(self, user_repo: Optional[UserRepository] = None):
        self.user_repo = user_repo or UserRepository()

    async def request_otp(self, phone_number: str) -> dict:
        logger.info("OTP requested", phone_number=phone_number)
        # In a real implementation, this would send OTP via SMS
        return {"message": "OTP sent successfully", "otp": "1234"}  # For development only

    async def verify_otp_and_login(self, verification: OTPVerification) -> TokenResponse:
        logger.info("Verifying OTP and logging in", phone_number=verification.phone_number)
        
        phone_number = verification.phone_number
        firebase_user = None
        
        # Try Firebase token verification first if provided
        if verification.firebase_token:
            logger.info("Verifying Firebase token")
            try:
                firebase_user = await verify_firebase_token(verification.firebase_token)
                if firebase_user:
                    phone_number = firebase_user.get("phone_number") or verification.phone_number
                    logger.info("Firebase token verified successfully", user_id=firebase_user.get("uid"))
                else:
                    logger.warning("Firebase token verification failed")
            except Exception as e:
                logger.error("Firebase token verification error", error=str(e))
        
        # If firebase not used or invalid, verify OTP
        if not firebase_user:
            logger.info("Verifying OTP code")
            if not verify_otp(verification.code):
                logger.warning("Invalid OTP code provided", phone_number=phone_number)
                raise BadRequestException("Invalid OTP code")
            logger.info("OTP code verified successfully")

        # Get or create user
        logger.info("Looking up user by phone", phone_number=phone_number)
        try:
            user = await self.user_repo.get_by_phone(phone_number)
            if not user:
                logger.info("Creating new user", phone_number=phone_number)
                user_data = {
                    "phone_number": phone_number,
                    "name": "",
                    "surname": ""
                }
                user = await self.user_repo.create_with_roles(user_data, [])
                logger.info("User created successfully", user_id=str(user.user_id))
            else:
                logger.info("Existing user found", user_id=str(user.user_id))
        except Exception as e:
            logger.error("Error with user repository operations", error=str(e))
            raise BadRequestException(f"User operation failed: {str(e)}")

        # Create access token
        try:
            access_token = create_access_token({"sub": str(user.user_id)})
            logger.info("Access token created successfully", user_id=str(user.user_id))
            return TokenResponse(
                access_token=access_token,
                expires_in=1440 * 60
            )
        except Exception as e:
            logger.error("Error creating access token", error=str(e))
            raise BadRequestException(f"Token creation failed: {str(e)}")
