
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class MongoDB:
    client = None
    
    @classmethod
    def connect(cls):
        """Establish connection to MongoDB"""
        try:
            cls.client = MongoClient(settings.MONGODB_URL)
            # Test the connection
            cls.client.admin.command('ping')
            logger.info("Successfully connected to MongoDB")
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    @classmethod
    def get_database(cls):
        """Get master database instance"""
        if cls.client is None:
            cls.connect()
        return cls.client[settings.DATABASE_NAME]
    
    @classmethod
    def close(cls):
        """Close database connection"""
        if cls.client:
            cls.client.close()
            logger.info("MongoDB connection closed")

# Helper function to get organizations collection
def get_organizations_collection():
    db = MongoDB.get_database()
    return db["organizations"]

# Helper function to get or create organization-specific collection
def get_org_collection(org_name: str):
    """
    Get organization-specific collection
    Returns tuple: (collection_object, collection_name)
    """
    db = MongoDB.get_database()
    # Sanitize organization name for collection naming
    collection_name = f"org_{org_name.lower().replace(' ', '_').replace('-', '_')}"
    return db[collection_name], collection_name
