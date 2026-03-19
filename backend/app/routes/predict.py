import time
import uuid
import logging
import os
from typing import Dict

from fastapi import APIRouter, UploadFile, File, Request, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from PIL import Image

from ..services.storage import save_upload
from ..services.model_loader import ModelService
from ..services.gradcam import generate_gradcam
from ..services.report_generator import report_generator
from ..services.dicom_handler import dicom_processor
from ..db import db
from ..config import settings
from ..models.prediction import PredictionResponse, InferenceRecord
from ..middleware.auth import require_doctor
from ..middleware.ratelimit import rate_limit_middleware
from ..models.user import UserInDB

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/predict", 
             response_model=PredictionResponse,
             status_code=status.HTTP_200_OK,
             summary="Run medical image prediction with Grad-CAM",
             description="""Production-ready prediction endpoint for medical image analysis.
             
             Accepts medical image upload, runs inference with loaded model,
             generates Grad-CAM visualization, and stores results in database.
             
             Medical audit compliant with proper error handling and logging.
             Requires doctor or admin role with rate limiting.
             """)
async def predict(request: Request, 
                  file: UploadFile = File(...),
                  current_user: UserInDB = Depends(require_doctor)) -> Dict:
    """Production-ready prediction endpoint.
    
    Medical audit compliant implementation with:
    - Proper request validation
    - Error handling with appropriate HTTP codes
    - Performance timing
    - Comprehensive logging
    - Database storage with required fields
    
    Args:
        request: FastAPI request object containing app state
        file: Uploaded medical image file
        
    Returns:
        PredictionResponse with all required fields
        
    Raises:
        HTTPException: For various error conditions with proper status codes
    """
    start_time = time.time()
    case_id = str(uuid.uuid4())
    
    # Check rate limit
    rate_limit_error = await rate_limit_middleware.check_rate_limit(request)
    if rate_limit_error:
        raise rate_limit_error
    
    logger.info(f"Starting prediction for case: {case_id} by user: {current_user.email}")
    
    # Enhanced file validation
    if not file.content_type:
        logger.warning(f"Missing content type for case {case_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File content type is required"
        )
    
    # Validate file type
    allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'application/dicom']
    is_dicom = file.content_type.lower() == 'application/dicom' or file.filename.lower().endswith('.dcm')
    
    if not is_dicom and file.content_type.lower() not in allowed_types:
        logger.warning(f"Invalid file type for case {case_id}: {file.content_type}")
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type. Allowed types: {', '.join(allowed_types)}"
        )
    
    # Validate file size (max 10MB)
    if file.size and file.size > 10 * 1024 * 1024:  # 10MB
        logger.warning(f"File too large for case {case_id}: {file.size} bytes")
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds 10MB limit"
        )
    
    # Save upload to local storage
    try:
        saved_path = save_upload(file)
        logger.debug(f"File saved to: {saved_path}")
    except Exception as e:
        logger.error(f"Failed to save upload for case {case_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save upload: {str(e)}"
        )
    
    # Load and validate image / process DICOM
    dicom_metadata = None
    try:
        if is_dicom:
            with open(saved_path, 'rb') as f:
                file_content = f.read()
            img, dicom_metadata, _ = dicom_processor.process_dicom_file(file_content)
            logger.debug(f"DICOM processed successfully. Modality: {dicom_metadata.get('Modality')}")
            # Ensure saved_path reflects the processed image so report_generator and gradcam work correctly
            from PIL import Image
            new_saved_path = saved_path.replace('.dcm', '.png') if saved_path.endswith('.dcm') else saved_path + '.png'
            img.save(new_saved_path)
            saved_path = new_saved_path
        else:
            from PIL import Image
            img = Image.open(saved_path).convert("RGB")
            logger.debug(f"Image loaded successfully: {img.size}")
    except Exception as e:
        logger.error(f"Invalid image/DICOM file for case {case_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file: {str(e)}"
        )
    
    # Get model service from app state (loaded once at startup)
    try:
        model_service: ModelService = request.app.state.model_service
        logger.debug(f"Using model service on device: {model_service.device}")
    except AttributeError:
        logger.error("Model service not found in app state")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Model service not initialized"
        )
    
    # Run inference
    try:
        input_tensor = model_service.preprocess(img)
        pred_index, probabilities, confidence, risk_score, explanation, birads, lesion, density, detections = model_service.predict(input_tensor, image_path=saved_path)
        logger.info(f"Prediction completed for case {case_id}: class={pred_index}")
    except Exception as e:
        logger.error(f"Prediction failed for case {case_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}"
        )
    
    # Generate Grad-CAM visualization
    try:
        gradcam_path = generate_gradcam(
            model_service.model, 
            input_tensor if not isinstance(model_service.model, BreastEnsemble) else [input_tensor]*4, 
            img, 
            target_class=pred_index
        )
        logger.debug(f"Grad-CAM generated: {gradcam_path}")
    except Exception as e:
        logger.error(f"Grad-CAM generation failed for case {case_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Grad-CAM generation failed: {str(e)}"
        )
    
    # Generate medical report
    try:
        report_path = report_generator.generate_medical_report(
            case_id=case_id,
            user_email=current_user.email,
            prediction_data={
                "prediction": "Malignant" if pred_index == 1 else "Benign",
                "confidence": confidence,
                "risk_score": risk_score,
                "explanation": explanation,
                "birads_class": birads,
                "lesion_type": lesion,
                "breast_density": density,
                "detections": detections
            },
            image_path=saved_path,
            gradcam_path=gradcam_path
        )
        logger.debug(f"Report generated: {report_path}")
    except Exception as e:
        logger.error(f"Report generation failed for case {case_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Report generation failed: {str(e)}"
        )

    # Create inference record for database
    inference_record = InferenceRecord(
        case_id=case_id,
        user_id=current_user.id,
        prediction="Malignant" if pred_index == 1 else "Benign",
        confidence=confidence,
        risk_score=risk_score,
        birads_class=birads,
        lesion_type=lesion,
        breast_density=density,
        explanation=explanation,
        image_url=f"/static/uploads/{os.path.basename(saved_path)}",
        gradcam_path=gradcam_path,
        report_path=report_path,
        model_version=model_service.model_version,
        metadata={
            "upload_path": saved_path,
            "image_size": img.size,
            "is_dummy_model": model_service.is_dummy_model,
            "dicom_metadata": dicom_metadata,
            "detections": detections
        }
    )
    
    # Store in MongoDB
    try:
        inserted_id = await db.insert_inference(inference_record.dict())
        logger.info(f"Inference record stored in database: {inserted_id}")
    except Exception as e:
        logger.error(f"Database storage failed for case {case_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database storage failed: {str(e)}"
        )
    
    # Calculate processing time
    latency_ms = int((time.time() - start_time) * 1000)
    logger.info(f"Prediction completed for case {case_id} in {latency_ms}ms")
    
    # Return response with all required fields
    response_data = PredictionResponse(
        id=inserted_id,
        case_id=case_id,
        prediction="Malignant" if pred_index == 1 else "Benign",
        confidence=confidence,
        risk_score=risk_score,
        birads_class=birads,
        lesion_type=lesion,
        breast_density=density,
        explanation=explanation,
        gradcam_url=gradcam_path,
        report_url=f"/static/reports/{os.path.basename(report_path)}",
        probabilities={str(i): float(p) for i, p in enumerate(probabilities)},
        model_version=model_service.model_version,
        latency_ms=latency_ms
    )
    
    # Add detections to the response manually as it's not in the Pydantic model yet or use dict()
    result_dict = response_data.dict()
    result_dict["detections"] = detections
    
    return JSONResponse(content=result_dict)


@router.get("/health", 
            summary="Health check endpoint",
            description="""Production-ready health monitoring endpoint.
            
            Returns service status, model information, and database connectivity.
            Medical audit compliant health reporting.
            """)
async def health_check(request: Request):
    """Health check endpoint for monitoring and medical audit compliance.
    
    Returns:
        HealthCheckResponse with service status information
    """
    import datetime
    
    try:
        # Check database connectivity
        db_status = "healthy"
        # Simple ping test
        if hasattr(db, 'client') and db.client:
            await db.client.admin.command('ping')
    except Exception:
        db_status = "unhealthy"
    
    # Get model service info
    try:
        model_service: ModelService = request.app.state.model_service
        model_info = model_service.get_model_info()
    except Exception:
        model_info = {"error": "Model service not available"}
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "model_info": model_info,
        "database_status": db_status
    }


@router.get("/statistics",
            summary="Get inference statistics",
            description="""Medical audit friendly statistics endpoint.
            
            Returns inference counts, model usage, and recent activity.
            """)
async def get_statistics():
    """Get inference statistics for monitoring and reporting.
    
    Medical audit compliant reporting endpoint.
    
    Returns:
        StatisticsResponse with inference metrics
    """
    try:
        stats = await db.get_inference_statistics()
        return stats
    except Exception as e:
        logger.error(f"Failed to retrieve statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve statistics"
        )


__all__ = ["router"]
