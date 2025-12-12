
from fastapi import HTTPException, status
from app.database import get_organizations_collection, get_org_collection, MongoDB
from app.utils.security import hash_password
from app.models.schemas import (
    OrganizationCreate, 
    OrganizationUpdate, 
    OrganizationResponse,
    MessageResponse
)
from datetime import datetime
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)

class OrganizationService:

    def __init__(self):
        self.orgs_collection = get_organizations_collection()
        self.db = MongoDB.get_database()
    
    def create_organization(self, org_data: OrganizationCreate) -> OrganizationResponse:

        logger.info(f"Creating organization: {org_data.organization_name}")
        
        # Check if organization name already exists
        existing_org = self.orgs_collection.find_one(
            {"organization_name": org_data.organization_name}
        )
        
        if existing_org:
            logger.warning(f"Organization already exists: {org_data.organization_name}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Organization '{org_data.organization_name}' already exists"
            )
        
        # Check if admin email already exists
        existing_email = self.orgs_collection.find_one(
            {"admin_email": org_data.email}
        )
        
        if existing_email:
            logger.warning(f"Email already registered: {org_data.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This email is already registered with another organization"
            )
        
        # Get or create organization-specific collection
        org_collection, collection_name = get_org_collection(org_data.organization_name)
        
        # Hash the admin password
        hashed_password = hash_password(org_data.password)
        
        # Prepare organization document
        org_document = {
            "organization_name": org_data.organization_name,
            "collection_name": collection_name,
            "admin_email": org_data.email,
            "admin_password": hashed_password,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Insert into master database
        result = self.orgs_collection.insert_one(org_document)
        
        # Explicitly create the collection (good practice)
        # This ensures the collection exists even if empty
        try:
            self.db.create_collection(collection_name)
            logger.info(f"Created collection: {collection_name}")
        except Exception as e:
            # Collection might already exist, which is fine
            logger.info(f"Collection {collection_name} already exists or created implicitly")
        
        logger.info(f"Organization created successfully: {org_data.organization_name}")
        
        return OrganizationResponse(
            organization_name=org_document["organization_name"],
            collection_name=org_document["collection_name"],
            admin_email=org_document["admin_email"],
            created_at=org_document["created_at"]
        )
    
    def get_organization(self, organization_name: str) -> OrganizationResponse:

        logger.info(f"Fetching organization: {organization_name}")
        
        organization = self.orgs_collection.find_one(
            {"organization_name": organization_name},
            {"admin_password": 0}  # Exclude password from response
        )
        
        if not organization:
            logger.warning(f"Organization not found: {organization_name}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Organization '{organization_name}' not found"
            )
        
        return OrganizationResponse(
            organization_name=organization["organization_name"],
            collection_name=organization["collection_name"],
            admin_email=organization["admin_email"],
            created_at=organization.get("created_at")
        )
    
    def update_organization(self, org_data: OrganizationUpdate, token_data: dict) -> MessageResponse:
     
        logger.info(f"Updating organization for email: {org_data.email}")
        
        # Find existing organization by admin email
        existing_org = self.orgs_collection.find_one(
            {"admin_email": org_data.email}
        )
        
        if not existing_org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found for this email"
            )
        
        # Verify the requesting user owns this organization
        if existing_org["admin_email"] != token_data["email"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to update this organization"
            )
        
        old_collection_name = existing_org["collection_name"]
        old_org_name = existing_org["organization_name"]
        
        # Check if new organization name already exists (if different)
        if org_data.organization_name != old_org_name:
            duplicate_check = self.orgs_collection.find_one(
                {"organization_name": org_data.organization_name}
            )
            if duplicate_check:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Organization name '{org_data.organization_name}' is already taken"
                )
        
        # Get new collection reference
        new_collection, new_collection_name = get_org_collection(org_data.organization_name)
        old_collection = self.db[old_collection_name]
        
        # Migrate data if collection name changed
        if old_collection_name != new_collection_name:
            logger.info(f"Migrating data from {old_collection_name} to {new_collection_name}")
            
            # Copy all documents from old to new collection
            document_count = old_collection.count_documents({})
            if document_count > 0:
                documents = list(old_collection.find({}))
                new_collection.insert_many(documents)
                logger.info(f"Migrated {document_count} documents")
            
            # Drop old collection
            old_collection.drop()
            logger.info(f"Dropped old collection: {old_collection_name}")
        
        # Update organization metadata
        update_data = {
            "organization_name": org_data.organization_name,
            "collection_name": new_collection_name,
            "admin_password": hash_password(org_data.password),
            "updated_at": datetime.utcnow()
        }
        
        self.orgs_collection.update_one(
            {"_id": existing_org["_id"]},
            {"$set": update_data}
        )
        
        logger.info(f"Organization updated successfully: {org_data.organization_name}")
        
        return MessageResponse(
            message="Organization updated successfully",
            details={
                "old_name": old_org_name,
                "new_name": org_data.organization_name,
                "old_collection": old_collection_name,
                "new_collection": new_collection_name
            }
        )
    
    def delete_organization(self, organization_name: str, token_data: dict) -> MessageResponse:

        logger.info(f"Deleting organization: {organization_name}")
        
        # Find the organization
        organization = self.orgs_collection.find_one(
            {"organization_name": organization_name}
        )
        
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Organization '{organization_name}' not found"
            )
        
        # Verify ownership - only the admin of this org can delete it
        if organization["admin_email"] != token_data["email"]:
            logger.warning(f"Unauthorized deletion attempt by {token_data['email']}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to delete this organization"
            )
        
        # Drop the organization's collection
        collection_name = organization["collection_name"]
        self.db[collection_name].drop()
        logger.info(f"Dropped collection: {collection_name}")
        
        # Delete organization from master database
        self.orgs_collection.delete_one({"_id": organization["_id"]})
        
        logger.info(f"Organization deleted successfully: {organization_name}")
        
        return MessageResponse(
            message=f"Organization '{organization_name}' deleted successfully",
            details={
                "organization_name": organization_name,
                "collection_deleted": collection_name
            }
        )
