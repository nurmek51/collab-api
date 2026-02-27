from fastapi import APIRouter, Depends, HTTPException
import structlog

from ..deps.auth import get_current_user
from ..models.user import User
from ..schemas.auth import OTPRequest, OTPVerification, RoleSelection, RefreshTokenRequest
from ..schemas.common import APIResponse
from ..services.auth import AuthService
from ..services.user import UserService
from ..exceptions.base import BadRequestException

logger = structlog.get_logger()
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/request-otp", response_model=APIResponse)
async def request_otp(
    request: OTPRequest,
):
    try:
        logger.info("OTP request received", phone_number=request.phone_number)
        auth_service = AuthService()
        result = await auth_service.request_otp(request.phone_number)
        logger.info("OTP request processed successfully")
        return APIResponse(success=True, data=result)
    except BadRequestException as e:
        logger.warning("Bad request in OTP", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Unexpected error in OTP request", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/verify-otp", response_model=APIResponse)
async def verify_otp(
    verification: OTPVerification,
):
    try:
        logger.info("OTP verification received", phone_number=verification.phone_number)
        auth_service = AuthService()
        result = await auth_service.verify_otp_and_login(verification)
        logger.info("OTP verification processed successfully")
        return APIResponse(success=True, data=result.model_dump())
    except BadRequestException as e:
        logger.warning("Bad request in OTP verification", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Unexpected error in OTP verification", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/refresh", response_model=APIResponse)
async def refresh_tokens(
    payload: RefreshTokenRequest,
):
    try:
        logger.info("Token refresh request received")
        auth_service = AuthService()
        result = await auth_service.refresh_access_token(payload.refresh_token)
        logger.info("Token refresh processed successfully")
        return APIResponse(success=True, data=result.model_dump())
    except BadRequestException as e:
        logger.warning("Bad request in token refresh", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Unexpected error in token refresh", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/select-role", response_model=APIResponse)
async def select_role(
    role_selection: RoleSelection,
    current_user: User = Depends(get_current_user),
):
    try:
        logger.info("Role selection received", user_id=str(current_user.user_id), role=role_selection.role)
        user_service = UserService()
        success = await user_service.add_role(current_user.user_id, role_selection.role)
        if success:
            logger.info("Role added successfully")
            return APIResponse(success=True, data={"message": f"Role {role_selection.role} added successfully"})
        else:
            logger.warning("Role already exists")
            return APIResponse(success=False, error="Role already exists")
    except Exception as e:
        logger.error("Unexpected error in role selection", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")
