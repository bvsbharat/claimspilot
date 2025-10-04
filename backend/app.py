"""
Main FastAPI application
Claims Triage System Backend
"""

import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

from api.routes import router
from services import get_pathway_pipeline, get_mongodb_service, get_pinecone_service, get_gmail_auto_fetch_service
from services.auto_transition import get_auto_transition_service

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown events
    """
    # Startup
    logger.info("Starting Claims Triage System API...")

    # Initialize MongoDB
    try:
        mongodb = await get_mongodb_service()
        logger.info("MongoDB connected")
    except Exception as e:
        logger.error(f"MongoDB connection failed: {e}")

    # Initialize Pinecone
    try:
        pinecone = get_pinecone_service()
        logger.info("Pinecone initialized")
    except Exception as e:
        logger.error(f"Pinecone initialization failed: {e}")

    # Initialize Pathway pipeline
    pathway_pipeline = get_pathway_pipeline()
    await pathway_pipeline.start_pipeline()

    logger.info("Pathway pipeline initialized")

    # Start auto-transition service
    auto_transition = get_auto_transition_service()
    await auto_transition.start()

    logger.info("Auto-transition service initialized")

    # Start Gmail auto-fetch service
    gmail_auto_fetch = get_gmail_auto_fetch_service()
    await gmail_auto_fetch.start()

    logger.info("Gmail auto-fetch service initialized")

    yield

    # Shutdown
    logger.info("Shutting down...")

    # Stop Gmail auto-fetch service
    try:
        gmail_auto_fetch = get_gmail_auto_fetch_service()
        await gmail_auto_fetch.stop()
    except:
        pass

    # Stop auto-transition service
    try:
        auto_transition = get_auto_transition_service()
        await auto_transition.stop()
    except:
        pass

    # Close MongoDB connection
    try:
        mongodb = await get_mongodb_service()
        await mongodb.close()
    except:
        pass


# Create FastAPI app
app = FastAPI(
    title="Claims Triage System API",
    description="Automated claims processing with intelligent routing",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router)

# Mount uploads directory for serving files
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8080))

    logger.info(f"Starting server on {host}:{port}")

    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )
