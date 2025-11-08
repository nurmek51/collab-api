import uuid

from fastapi import APIRouter, Depends, Path

from ..services.company import CompanyService
from ..services.client import ClientService
from ..schemas.company import CompanyCreate, CompanyUpdate
from ..schemas.common import APIResponse
from ..deps.auth import get_current_user, require_client
from ..models.user import User

router = APIRouter(prefix="/companies", tags=["Companies"])


async def get_company_service() -> CompanyService:
    return CompanyService()


async def get_client_service() -> ClientService:
    return ClientService()


@router.get("/", response_model=APIResponse)
async def get_all_companies(
    current_user: User = Depends(get_current_user),
    company_service: CompanyService = Depends(get_company_service),
):
    try:
        companies = await company_service.get_all_companies()
        return APIResponse(success=True, data=companies)
    except Exception as e:
        return APIResponse(success=False, error=str(e))


@router.post("/", response_model=APIResponse)
async def create_company(
    company_data: CompanyCreate,
    current_user: User = Depends(require_client()),
    company_service: CompanyService = Depends(get_company_service),
    client_service: ClientService = Depends(get_client_service),
):
    try:
        client = await client_service.get_client_by_user_id(current_user.user_id)
        company = await company_service.create_company(client.client_id, company_data)
        return APIResponse(success=True, data=company)
    except Exception as e:
        return APIResponse(success=False, error=str(e))


@router.get("/my", response_model=APIResponse)
async def get_my_companies(
    current_user: User = Depends(require_client()),
    company_service: CompanyService = Depends(get_company_service),
    client_service: ClientService = Depends(get_client_service),
):
    try:
        client = await client_service.get_client_by_user_id(current_user.user_id)
        companies = await company_service.get_companies_by_client(client.client_id)
        return APIResponse(success=True, data=companies)
    except Exception as e:
        return APIResponse(success=False, error=str(e))


@router.get("/id/{company_id}", response_model=APIResponse)
async def get_company(
    company_id: uuid.UUID = Path(...),
    current_user: User = Depends(get_current_user),
    company_service: CompanyService = Depends(get_company_service),
):
    try:
        company = await company_service.get_company(company_id)
        return APIResponse(success=True, data=company)
    except Exception as e:
        return APIResponse(success=False, error=str(e))


@router.get("/{client_id}", response_model=APIResponse)
async def get_companies_for_client(
    client_id: uuid.UUID = Path(...),
    current_user: User = Depends(get_current_user),
    company_service: CompanyService = Depends(get_company_service),
):
    try:
        companies = await company_service.get_companies_by_client(client_id)
        return APIResponse(success=True, data=companies)
    except Exception as e:
        return APIResponse(success=False, error=str(e))


@router.put("/id/{company_id}", response_model=APIResponse)
async def update_company(
    company_id: uuid.UUID = Path(...),
    company_update: CompanyUpdate = ...,
    current_user: User = Depends(require_client()),
    company_service: CompanyService = Depends(get_company_service),
):
    try:
        updated_company = await company_service.update_company(company_id, company_update)
        return APIResponse(success=True, data=updated_company)
    except Exception as e:
        return APIResponse(success=False, error=str(e))
