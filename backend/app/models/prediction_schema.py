"""
Structured Prediction Schema for Medical AI Reporting System

Hospital-grade Pydantic models for prediction output with risk scoring,
findings detection, and model metadata tracking.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


class RiskCategory(str, Enum):
    """Risk category classification based on numeric score."""
    LOW_RISK = "Low Risk"
    MODERATE_RISK = "Moderate Risk"
    HIGH_RISK = "High Risk"
    VERY_HIGH_RISK = "Very High Risk"


class PredictionLabel(str, Enum):
    """Medical prediction classification labels."""
    BENIGN = "Benign"
    SUSPICIOUS = "Suspicious"
    MALIGNANT = "Malignant"


class FindingsBase(BaseModel):
    """Detected findings from medical image analysis."""
    mass_detected: bool = Field(..., description="Mass/lesion detected in image")
    calcifications: Optional[str] = Field(None, description="Calcification pattern if detected")
    asymmetry: Optional[str] = Field(None, description="Asymmetry findings if present")
    architectural_distortion: bool = Field(False, description="Architectural distortion detected")
    density: Optional[str] = Field(None, description="Breast density classification")
    additional_findings: Optional[List[str]] = Field(default_factory=list, description="Additional observations")


class ExplainabilityData(BaseModel):
    """Model explainability data including Grad-CAM heatmap."""
    heatmap_path: str = Field(..., description="Path to Grad-CAM heatmap image")
    attention_region: Optional[str] = Field(None, description="Primary attention region location")
    heatmap_confidence: Optional[float] = Field(None, description="Heatmap generation confidence score")


class ModelMetadata(BaseModel):
    """Model information for transparency and audit trail."""
    model_name: str = Field(..., description="Name of the ML model used")
    dataset: str = Field(..., description="Training dataset source")
    version: str = Field(..., description="Model version identifier")
    sensitivity: Optional[float] = Field(None, description="Model sensitivity metric")
    specificity: Optional[float] = Field(None, description="Model specificity metric")
    auc_score: Optional[float] = Field(None, description="Area under ROC curve")


class PredictionData(BaseModel):
    """Core prediction output with confidence and risk assessment."""
    label: PredictionLabel = Field(..., description="Prediction classification")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Model confidence score")
    risk_score: int = Field(..., ge=0, le=100, description="Numeric risk score 0-100")
    risk_category: RiskCategory = Field(..., description="Risk category classification")
    probability_benign: float = Field(..., ge=0.0, le=1.0, description="Probability of benign")
    probability_malignant: float = Field(..., ge=0.0, le=1.0, description="Probability of malignant")


class PredictionOutput(BaseModel):
    """Complete structured prediction output for medical reporting."""
    prediction: PredictionData = Field(..., description="Prediction results with confidence")
    findings: FindingsBase = Field(..., description="Detected imaging findings")
    explainability: ExplainabilityData = Field(..., description="Model explainability data")
    model_info: ModelMetadata = Field(..., description="Model metadata for transparency")
    
    class Config:
        json_schema_extra = {
            "example": {
                "prediction": {
                    "label": "Suspicious",
                    "confidence": 0.87,
                    "risk_score": 72,
                    "risk_category": "High Risk",
                    "probability_benign": 0.13,
                    "probability_malignant": 0.87
                },
                "findings": {
                    "mass_detected": True,
                    "calcifications": "Clustered",
                    "asymmetry": "Present",
                    "architectural_distortion": False,
                    "density": "Scattered",
                    "additional_findings": []
                },
                "explainability": {
                    "heatmap_path": "static/gradcam/gradcam_abc123.png",
                    "attention_region": "Upper Outer Quadrant",
                    "heatmap_confidence": 0.92
                },
                "model_info": {
                    "model_name": "EfficientNet-B4",
                    "dataset": "CBIS-DDSM + BreastMNIST",
                    "version": "v1.0.0",
                    "sensitivity": 0.94,
                    "specificity": 0.91,
                    "auc_score": 0.96
                }
            }
        }


class DoctorSummary(BaseModel):
    """Clinical report section in professional radiology language."""
    technical_findings: str = Field(..., description="Technical imaging findings")
    interpretation: str = Field(..., description="Clinical interpretation summary")
    limitations: str = Field(..., description="Model limitations and caveats")
    recommendation: str = Field(..., description="Suggested next steps")
    confidence_assessment: str = Field(..., description="Assessment of prediction confidence")
    
    class Config:
        json_schema_extra = {
            "example": {
                "technical_findings": "A mass is identified in the upper outer quadrant of the left breast...",
                "interpretation": "The imaging findings demonstrate features suspicious for malignancy...",
                "limitations": "This AI-assisted analysis has a reported sensitivity of 94% and may produce false positives...",
                "recommendation": "Correlation with clinical examination and additional imaging (magnification views) is recommended...",
                "confidence_assessment": "The model demonstrates high confidence (87%) in this prediction..."
            }
        }


class PatientSummary(BaseModel):
    """Patient-friendly report section in plain language."""
    main_result: str = Field(..., description="Main result in simple terms")
    what_it_means: str = Field(..., description="Plain language explanation of the score")
    next_steps: str = Field(..., description="Clear guidance on next actions")
    reassurance: str = Field(..., description="Calming, non-alarming message")
    questions_to_ask: Optional[List[str]] = Field(None, description="Questions patient can ask doctor")
    
    class Config:
        json_schema_extra = {
            "example": {
                "what_it_means": "Your screening shows some areas that need closer look...",
                "next_steps": "Your doctor will discuss these results with you...",
                "reassurance": "Many findings that look concerning turn out to be benign...",
                "questions_to_ask": [
                    "What type of additional testing do I need?",
                    "How soon should I schedule follow-up?",
                    "What are my options if this is cancer?"
                ]
            }
        }


class ComplianceInfo(BaseModel):
    """Required compliance and disclaimer information."""
    ai_limitation_statement: str = Field(..., description="AI system limitations disclaimer")
    medical_disclaimer: str = Field(..., description="Not a medical diagnosis statement")
    data_usage_statement: str = Field(..., description="Data handling and privacy notice")
    model_transparency: str = Field(..., description="Model transparency information")
    dataset_attribution: str = Field(..., description="Training dataset source attribution")
    version: str = Field(..., description="Report version for compliance tracking")


class ReportMetadata(BaseModel):
    """Report metadata for tracking and audit."""
    report_id: str = Field(..., description="Unique report identifier (UUID)")
    case_id: str = Field(..., description="Associated case identifier")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Report generation timestamp")
    patient_id: Optional[str] = Field(None, description="Patient identifier (if provided)")
    institution: Optional[str] = Field(None, description="Institution/clinic name")
    radiologist: Optional[str] = Field(None, description="Reviewing radiologist name")


class MedicalReport(BaseModel):
    """Complete medical report structure."""
    metadata: ReportMetadata = Field(..., description="Report metadata")
    prediction: PredictionData = Field(..., description="Prediction results")
    findings: FindingsBase = Field(..., description="Detected findings")
    explainability: ExplainabilityData = Field(..., description="Model explainability")
    model_info: ModelMetadata = Field(..., description="Model information")
    doctor_summary: DoctorSummary = Field(..., description="Clinical report section")
    patient_summary: PatientSummary = Field(..., description="Patient-friendly section")
    compliance: ComplianceInfo = Field(..., description="Compliance and disclaimer section")
    pdf_path: Optional[str] = Field(None, description="Path to generated PDF file")
    html_path: Optional[str] = Field(None, description="Path to HTML preview")
    
    class Config:
        json_schema_extra = {
            "example": {
                "metadata": {
                    "report_id": "rpt_12345678-1234-1234-1234-123456789abc",
                    "case_id": "case_abc123",
                    "created_at": "2024-01-15T10:30:00Z"
                },
                "prediction": {
                    "label": "Suspicious",
                    "confidence": 0.87,
                    "risk_score": 72,
                    "risk_category": "High Risk",
                    "probability_benign": 0.13,
                    "probability_malignant": 0.87
                }
            }
        }


class ReportStorageRecord(BaseModel):
    """MongoDB storage model for medical reports."""
    report_id: str = Field(..., description="Unique report identifier")
    case_id: str = Field(..., description="Associated case ID")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    prediction_data: Dict[str, Any] = Field(..., description="Serialized prediction data")
    doctor_summary: str = Field(..., description="Clinical summary text")
    patient_summary: str = Field(..., description="Patient summary text")
    pdf_path: Optional[str] = Field(None, description="PDF file path")
    model_version: str = Field(..., description="Model version used")
    user_id: Optional[str] = Field(None, description="User who generated report")


__all__ = [
    "RiskCategory",
    "PredictionLabel",
    "FindingsBase",
    "ExplainabilityData",
    "ModelMetadata",
    "PredictionData",
    "PredictionOutput",
    "DoctorSummary",
    "PatientSummary",
    "ComplianceInfo",
    "ReportMetadata",
    "MedicalReport",
    "ReportStorageRecord"
]