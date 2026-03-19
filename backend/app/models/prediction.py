from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import datetime


class PredictionRequest(BaseModel):
    """Request model for prediction endpoint.
    
    Medical audit compliant request validation.
    """
    # File upload is handled via FastAPI UploadFile
    # This model is for additional request parameters if needed
    pass


class PredictionResponse(BaseModel):
    """Response model for prediction endpoint.
    
    Production-ready response structure with all required fields.
    Medical audit compliant with clear data types.
    """
    id: str = Field(..., description="Database record ID")
    case_id: str = Field(..., description="Unique case identifier")
    prediction: str = Field(..., description="Predicted class (Malignant/Benign)")
    confidence: float = Field(..., description="Prediction confidence (0.0-1.0)")
    risk_score: int = Field(..., description="Risk score (0-100)")
    birads_class: str = Field(..., description="BI-RADS classification (0-6)")
    lesion_type: str = Field(..., description="Lesion type (Mass, Calcification, etc.)")
    breast_density: str = Field(..., description="Breast density classification (A, B, C, D)")
    explanation: str = Field(..., description="AI explanation of prediction")
    gradcam_url: str = Field(..., description="URL to Grad-CAM overlay image")
    report_url: str = Field(..., description="URL to PDF report")
    probabilities: Dict[str, float] = Field(..., description="Class probabilities")
    model_version: str = Field(..., description="Model version identifier")
    latency_ms: int = Field(..., description="Processing time in milliseconds")
    timestamp: Optional[str] = Field(None, description="ISO format timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "case_id": "case_1234567890abcdef",
                "prediction": "Malignant",
                "confidence": 0.85,
                "risk_score": 75,
                "birads_class": "4",
                "lesion_type": "Mass",
                "breast_density": "C",
                "probabilities": {"0": 0.15, "1": 0.85},
                "gradcam_path": "/static/gradcam/gradcam_abc123.png",
                "model_version": "v1.0.0",
                "latency_ms": 150,
                "timestamp": "2024-01-15T10:30:00.000Z"
            }
        }


class InferenceRecord(BaseModel):
    """Database record model for inference storage.
    
    Medical audit compliant structure matching database requirements:
    - case_id
    - timestamp
    - prediction
    - confidence
    - risk_score
    - explanation
    - gradcam_path
    - report_path
    - model_version
    - user_id
    - doctor_note
    - doctor_status
    - admin_status
    - birads_class
    - lesion_type
    - breast_density
    """
    case_id: str = Field(..., description="Unique case identifier")
    user_id: str = Field(..., description="ID of user who submitted")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="UTC timestamp")
    prediction: str = Field(..., description="Predicted class (Malignant/Benign)")
    confidence: float = Field(..., description="Prediction confidence (0.0-1.0)")
    risk_score: int = Field(..., description="Risk score (0-100)")
    birads_class: str = Field(..., description="BI-RADS classification (0-6)")
    lesion_type: str = Field(..., description="Lesion type (Mass, Calcification, etc.)")
    breast_density: str = Field(..., description="Breast density classification (A, B, C, D)")
    explanation: str = Field(..., description="AI explanation of prediction")
    image_url: str = Field(..., description="URL to original uploaded image")
    gradcam_path: str = Field(..., description="Path to Grad-CAM image")
    report_path: str = Field(..., description="Path to PDF report")
    doctor_note: Optional[str] = Field(None, description="Doctor's notes")
    doctor_status: Optional[str] = Field(None, description="Doctor status (null, confirmed, rejected)")
    admin_status: Optional[str] = Field(None, description="Admin status")
    model_version: str = Field(..., description="Model version identifier")
    metadata: Optional[Dict] = Field(default=None, description="Additional metadata")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class StatisticsResponse(BaseModel):
    """Response model for inference statistics.
    
    Medical audit friendly reporting structure.
    """
    total_inferences: int = Field(..., description="Total number of inferences")
    recent_24h_count: int = Field(..., description="Inferences in last 24 hours")
    model_version_distribution: List[Dict[str, int]] = Field(..., description="Model usage statistics")
    timestamp: str = Field(..., description="Report generation timestamp")


class HealthCheckResponse(BaseModel):
    """Response model for health check endpoint.
    
    Production-ready health monitoring.
    """
    status: str = Field(..., description="Service status")
    timestamp: str = Field(..., description="Current timestamp")
    version: str = Field(..., description="Service version")
    model_info: Dict = Field(..., description="Model service information")
    database_status: str = Field(..., description="Database connection status")


# Export all models
__all__ = [
    "PredictionRequest",
    "PredictionResponse",
    "InferenceRecord",
    "StatisticsResponse",
    "HealthCheckResponse"
]