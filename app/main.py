
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.config import settings
from app.database import MongoDB
from app.routers import auth, organization

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handle startup and shutdown events
    """
    # Startup
    logger.info("Starting Organization Management Service...")
    MongoDB.connect()
    logger.info("Database connection established")
    yield
    # Shutdown
    logger.info("Shutting down...")
    MongoDB.close()
    logger.info("Database connection closed")

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="A multi-tenant organization management service with JWT authentication",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(organization.router)

# Root endpoint
@app.get("/", tags=["Root"])
async def root():

    return {
        "message": "Organization Management Service API",
        "version": "1.0.0",
        "status": "active",
        "docs": "/docs"
    }

# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    
    try:
        # Test database connection
        db = MongoDB.get_database()
        db.command('ping')
        return {
            "status": "healthy",
            "database": "connected"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
