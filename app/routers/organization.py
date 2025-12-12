
from fastapi import APIRouter, Depends, Query
from app.models.schemas import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationResponse,
    MessageResponse
)
from app.services.org_service import OrganizationService
from app.utils.jwt_handler import verify_token
from typing import Dict

router = APIRouter(
    prefix="/org",
    tags=["Organizations"]
)

@router.post("/create", response_model=OrganizationResponse, status_code=201)
async def create_organization(org_data: OrganizationCreate):
 
    org_service = OrganizationService()
    return org_service.create_organization(org_data)

@router.get("/get", response_model=OrganizationResponse)
async def get_organization(
    organization_name: str = Query(..., description="Name of the organization to retrieve")
):

    org_service = OrganizationService()
    return org_service.get_organization(organization_name)

@router.put("/update", response_model=MessageResponse)
async def update_organization(
    org_data: OrganizationUpdate,
    token_data: Dict = Depends(verify_token)
):

    org_service = OrganizationService()
    return org_service.update_organization(org_data, token_data)

@router.delete("/delete", response_model=MessageResponse)
async def delete_organization(
    organization_name: str = Query(..., description="Name of the organization to delete"),
    token_data: Dict = Depends(verify_token)
):

    org_service = OrganizationService()
    return org_service.delete_organization(organization_name, token_data)
