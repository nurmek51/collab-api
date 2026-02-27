import uuid
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List
from ..config.auth import verify_token
from ..models.user import User
from ..exceptions import UnauthorizedException, ForbiddenException
from ..repositories.user import UserRepository

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> User:
    token = credentials.credentials
    payload = verify_token(token, expected_type="access")
    
    if payload is None:
        raise UnauthorizedException("Invalid token")
    
    user_id = payload.get("sub")
    if user_id is None:
        raise UnauthorizedException("Invalid token")

    try:
        uuid_user_id = uuid.UUID(str(user_id))
    except ValueError as exc:
        raise UnauthorizedException("Invalid token") from exc

    user_repo = UserRepository()
    user = await user_repo.get_by_id(uuid_user_id)

    if not user:
        raise UnauthorizedException("User not found")
    return user


async def get_current_user_roles(
    user: User = Depends(get_current_user)
) -> List[str]:
    return list(user.roles)


def require_role(required_role: str):
    async def role_checker(
        user: User = Depends(get_current_user),
        roles: List[str] = Depends(get_current_user_roles)
    ) -> User:
        if required_role not in roles:
            raise ForbiddenException(f"Role '{required_role}' required")
        return user
    return role_checker


def require_admin():
    return require_role("admin")


def require_freelancer():
    return require_role("freelancer")


def require_client():
    return require_role("client")
