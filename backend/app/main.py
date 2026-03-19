import os
import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from .routes import predict_router, auth_router, reporting_router
from .routes.dicomweb import router as dicomweb_router
from .config import settings
from .services.model_loader import ModelService
from .db import db
from .middleware.logging import RequestLoggingMiddleware, ModelAuditMiddleware
from .middleware.exceptions import exception_handlers
from .middleware.ratelimit import limiter, rate_limit_middleware

# Configure logging for medical audit compliance
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        # Add file handler for audit trail in production
        # logging.FileHandler('aviothic_audit.log')
    ]
)

logger = logging.getLogger(__name__)

# Production-ready FastAPI application
# Medical audit compliant with proper startup/shutdown handling
app = FastAPI(
    title="Aviothic AI Medical Imaging Platform",
    description="""Production-ready medical AI platform with Grad-CAM visualization.
    
    Features:
    - Single model load at startup (not per request)
    - Real Grad-CAM implementation with PyTorch gradients
    - MongoDB storage with proper audit trail
    - Medical audit compliant logging and error handling
    - Static file serving for Grad-CAM images
    - JWT authentication with role-based access control
    - Rate limiting and security hardening
    
    DUMMY MODEL WARNING: Current implementation uses dummy model for demonstration.
    Replace with real trained medical model for production deployment.
    """,
    version=settings.MODEL_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    exception_handlers=exception_handlers
)

# Configure CORS for medical application security
# Production-hardened CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    expose_headers=["X-Request-ID"]
)

# Add security and monitoring middleware
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(ModelAuditMiddleware)


@app.on_event("startup")
async def startup_event():
    """Production-ready startup sequence.
    
    Medical audit compliant initialization:
    1. Ensure required directories exist
    2. Connect to MongoDB database
    3. Load ML model once (single load pattern)
    4. Initialize logging and monitoring
    
    DUMMY MODEL WARNING: Model loading includes clear dummy model detection.
    """
    logger.info("Starting Aviothic AI Backend...")
    
    # Ensure all required static directories exist
    directories_to_create = [
        settings.STATIC_DIR,
        settings.UPLOAD_DIR,
        settings.GRADCAM_DIR
    ]
    
    for directory in directories_to_create:
        os.makedirs(directory, exist_ok=True)
        logger.debug(f"Ensured directory exists: {directory}")
    
    # Connect to MongoDB database
    try:
        await db.connect()
        logger.info("Database connection established")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise
    
    # Load model service once at startup (production pattern)
    # This ensures model is loaded only once, not per request
    try:
        app.state.model_service = ModelService(device=settings.DEVICE)
        model_info = app.state.model_service.get_model_info()
        logger.info(f"Model service loaded: {model_info}")
        
        # Medical audit warning for dummy model
        if model_info.get("is_dummy_model"):
            logger.warning("DUMMY MODEL IN USE - NOT FOR MEDICAL PRODUCTION")
            logger.warning("Replace with real trained medical model before deployment")
        
    except Exception as e:
        logger.error(f"Failed to load model service: {e}")
        raise
    
    logger.info("Aviothic AI Backend startup completed successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Graceful shutdown sequence.
    
    Medical audit compliant cleanup:
    1. Close database connections
    2. Cleanup resources
    3. Log shutdown event
    """
    logger.info("Shutting down Aviothic AI Backend...")
    
    # Close database connection
    try:
        await db.close()
        logger.info("Database connection closed")
    except Exception as e:
        logger.error(f"Error during database shutdown: {e}")
    
    logger.info("Aviothic AI Backend shutdown completed")


# Mount static files for Grad-CAM image serving
# Serves files from /static/gradcam/ and /static/uploads/
app.mount("/static", StaticFiles(directory=settings.STATIC_DIR), name="static")

# Include API routes with proper prefixing
app.include_router(auth_router, prefix="/api/v1")
app.include_router(predict_router, prefix="/api/v1")
app.include_router(reporting_router, prefix="/api/v1")
app.include_router(dicomweb_router, prefix="/api/v1")


# Health check endpoint at root level
@app.get("/", 
         summary="Root endpoint",
         description="""Medical audit compliant root endpoint.
         
         Returns basic service information and status.
         """)
async def root():
    return {
        "service": "Aviothic AI Medical Imaging Platform",
        "version": settings.MODEL_VERSION,
        "status": "operational",
        "documentation": "/api/docs",
        "warning": "DUMMY MODEL IN USE - NOT FOR MEDICAL PRODUCTION" if \
                  hasattr(app.state, 'model_service') and \
                  app.state.model_service.is_dummy_model else "Ready for production"
    }


if __name__ == "__main__":
    """Entry point for running the application directly.
    
    Production deployment should use: uvicorn app.main:app --host 0.0.0.0 --port 8000
    """
    logger.info("Starting server directly (use uvicorn for production)")
    uvicorn.run(
        "app.main:app", 
        host=settings.HOST, 
        port=settings.PORT, 
        reload=settings.DEBUG,  # Only enable reload in development
        log_level=settings.LOG_LEVEL.lower()
    )