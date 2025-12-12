
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime

class OrganizationCreate(BaseModel):
    
    organization_name: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    
    @field_validator('organization_name')
    @classmethod
    def validate_org_name(cls, v):
        
        v = v.strip()
        if not v.replace(' ', '').replace('-', '').replace('_', '').isalnum():
            raise ValueError('Organization name can only contain letters, numbers, spaces, hyphens, and underscores')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "organization_name": "TechCorp",
                "email": "admin@techcorp.com",
                "password": "SecurePass123"
            }
        }

class OrganizationUpdate(BaseModel):
    """Schema for updating an organization"""
    organization_name: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    
    @field_validator('organization_name')
    @classmethod
    def validate_org_name(cls, v):
        v = v.strip()
        if not v.replace(' ', '').replace('-', '').replace('_', '').isalnum():
            raise ValueError('Organization name can only contain letters, numbers, spaces, hyphens, and underscores')
        return v

class OrganizationResponse(BaseModel):
    """Schema for organization response"""
    organization_name: str
    collection_name: str
    admin_email: str
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class AdminLogin(BaseModel):
    """Schema for admin login"""
    email: EmailStr
    password: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "admin@techcorp.com",
                "password": "SecurePass123"
            }
        }

class TokenResponse(BaseModel):
   
    access_token: str
    token_type: str = "bearer"
    organization_name: str
    admin_email: str

class MessageResponse(BaseModel):

    message: str
    details: Optional[dict] = None
