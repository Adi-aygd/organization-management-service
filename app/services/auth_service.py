
from fastapi import HTTPException, status
from app.database import get_organizations_collection
from app.utils.security import verify_password
from app.utils.jwt_handler import create_access_token
from app.models.schemas import AdminLogin, TokenResponse
import logging

logger = logging.getLogger(__name__)

class AuthService:
  
    
    def __init__(self):
        self.orgs_collection = get_organizations_collection()
    
    def authenticate_admin(self, login_data: AdminLogin) -> TokenResponse:
  
        logger.info(f"Authentication attempt for email: {login_data.email}")
        
        # Find organization by admin email
        organization = self.orgs_collection.find_one(
            {"admin_email": login_data.email}
        )
        
        if not organization:
            logger.warning(f"Login failed: Email not found - {login_data.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Verify password
        if not verify_password(login_data.password, organization["admin_password"]):
            logger.warning(f"Login failed: Invalid password for {login_data.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Create JWT token
        token_data = {
            "email": organization["admin_email"],
            "org_id": str(organization["_id"]),
            "organization_name": organization["organization_name"]
        }
        
        access_token = create_access_token(token_data)
        
        logger.info(f"Login successful for {login_data.email}")
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            organization_name=organization["organization_name"],
            admin_email=organization["admin_email"]
        )
