
from fastapi import APIRouter, Depends
from app.models.schemas import AdminLogin, TokenResponse
from app.services.auth_service import AuthService

router = APIRouter(
    prefix="/admin",
    tags=["Authentication"]
)

@router.post("/login", response_model=TokenResponse)
async def admin_login(login_data: AdminLogin):
   
    auth_service = AuthService()
    return auth_service.authenticate_admin(login_data)
