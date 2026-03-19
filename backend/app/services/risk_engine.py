"""
Risk Scoring Engine for Medical AI Predictions

Implements numeric risk scoring (0-100) derived from model probabilities
and weighted abnormal feature detection with category mapping.
"""

import logging
from typing import Dict, Tuple, Optional
from datetime import datetime

from ..models.prediction_schema import (
    RiskCategory, 
    PredictionLabel, 
    PredictionData,
    FindingsBase
)

logger = logging.getLogger(__name__)


class RiskEngine:
    """
    Production-ready risk scoring engine for medical AI predictions.
    
    Calculates numeric risk score (0-100) based on:
    - Model probability outputs
    - Detected abnormal features weights
    - Clinical risk factors
    
    Category Mapping:
    - 0-30: Low Risk
    - 31-60: Moderate Risk  
    - 61-80: High Risk
    - 81-100: Very High Risk
    """
    
    # Feature weight configurations for risk calculation
    FEATURE_WEIGHTS = {
        "mass_detected": 25,
        "calcifications": 20,
        "asymmetry": 15,
        "architectural_distortion": 30,
    }
    
    # Breast region risk multipliers
    REGION_RISK_MULTIPLIERS = {
        "upper_outer_quadrant": 1.2,
        "upper_inner_quadrant": 1.0,
        "lower_outer_quadrant": 1.1,
        "lower_inner_quadrant": 1.0,
        "central": 1.3,
        "axillary_tail": 1.15,
        "multifocal": 1.4,
        "diffuse": 1.5,
    }
    
    # Model performance adjustment factors
    MODEL_PERFORMANCE_FACTORS = {
        "high_confidence": 0.95,    # >90% confidence
        "medium_confidence": 1.0,    # 70-90% confidence
        "low_confidence": 1.1,      # <70% confidence
    }
    
    def __init__(self):
        self.min_risk_score = 0
        self.max_risk_score = 100
        
    def calculate_risk_score(
        self,
        probability_malignant: float,
        findings: FindingsBase,
        model_confidence: float,
        attention_region: Optional[str] = None
    ) -> Tuple[int, RiskCategory]:
        """
        Calculate risk score and category from prediction data.
        
        Args:
            probability_malignant: Model probability (0-1) for malignant
            findings: Detected imaging findings
            model_confidence: Model confidence in prediction
            attention_region: Region where model focused (if known)
            
        Returns:
            Tuple of (risk_score: int, risk_category: RiskCategory)
        """
        # Base risk from probability
        base_risk = probability_malignant * 100
        
        # Add feature-based risk contributions
        feature_risk = self._calculate_feature_risk(findings)
        
        # Apply region multiplier if available
        region_multiplier = 1.0
        if attention_region:
            region_multiplier = self._get_region_multiplier(attention_region)
        
        # Apply confidence adjustment
        confidence_factor = self._get_confidence_factor(model_confidence)
        
        # Calculate final risk score
        raw_risk = (base_risk * 0.5) + (feature_risk * 0.35) + (base_risk * region_multiplier * 0.15)
        raw_risk *= confidence_factor
        
        # Clamp to valid range
        risk_score = int(max(self.min_risk_score, min(self.max_risk_score, raw_risk)))
        
        # Determine category
        risk_category = self._get_risk_category(risk_score)
        
        logger.info(
            f"Risk score calculated: {risk_score} ({risk_category.value}) "
            f"from prob={probability_malignant:.2f}, features={feature_risk:.1f}, "
            f"region_mult={region_multiplier}, conf_factor={confidence_factor}"
        )
        
        return risk_score, risk_category
    
    def _calculate_feature_risk(self, findings: FindingsBase) -> float:
        """Calculate risk contribution from detected features."""
        feature_risk = 0.0
        
        if findings.mass_detected:
            feature_risk += self.FEATURE_WEIGHTS["mass_detected"]
            
        if findings.calcifications:
            calc_risk = self._assess_calcifications(findings.calcifications)
            feature_risk += calc_risk
            
        if findings.asymmetry:
            feature_risk += self.FEATURE_WEIGHTS["asymmetry"]
            
        if findings.architectural_distortion:
            feature_risk += self.FEATURE_WEIGHTS["architectural_distortion"]
            
        return feature_risk
    
    def _assess_calcifications(self, calc_type: str) -> float:
        """Assess risk level based on calcification pattern."""
        calc_risk_map = {
            "punctate": 10,
            " amorphous": 15,
            "coarse": 20,
            "dystrophic": 20,
            "milk_of_calcium": 5,
            "rodlike": 10,
            "clustered": 35,
            "linear": 40,
            "segmental": 45,
        }
        
        return calc_risk_map.get(calc_type.lower().strip(), 20)
    
    def _get_region_multiplier(self, region: str) -> float:
        """Get risk multiplier based on breast region."""
        region_lower = region.lower().strip()
        
        for region_key, multiplier in self.REGION_RISK_MULTIPLIERS.items():
            if region_key in region_lower:
                return multiplier
                
        return 1.0
    
    def _get_confidence_factor(self, confidence: float) -> float:
        """Get confidence adjustment factor."""
        if confidence > 0.9:
            return self.MODEL_PERFORMANCE_FACTORS["high_confidence"]
        elif confidence >= 0.7:
            return self.MODEL_PERFORMANCE_FACTORS["medium_confidence"]
        else:
            return self.MODEL_PERFORMANCE_FACTORS["low_confidence"]
    
    def _get_risk_category(self, risk_score: int) -> RiskCategory:
        """Map numeric score to risk category."""
        if risk_score <= 30:
            return RiskCategory.LOW_RISK
        elif risk_score <= 60:
            return RiskCategory.MODERATE_RISK
        elif risk_score <= 80:
            return RiskCategory.HIGH_RISK
        else:
            return RiskCategory.VERY_HIGH_RISK
    
    def create_prediction_data(
        self,
        label: PredictionLabel,
        confidence: float,
        probability_benign: float,
        probability_malignant: float,
        findings: FindingsBase,
        attention_region: Optional[str] = None
    ) -> PredictionData:
        """
        Create complete prediction data with risk assessment.
        
        Args:
            label: Prediction classification label
            confidence: Model confidence score
            probability_benign: Probability of benign
            probability_malignant: Probability of malignant
            findings: Detected imaging findings
            attention_region: Model attention region
            
        Returns:
            Complete PredictionData object
        """
        risk_score, risk_category = self.calculate_risk_score(
            probability_malignant=probability_malignant,
            findings=findings,
            model_confidence=confidence,
            attention_region=attention_region
        )
        
        return PredictionData(
            label=label,
            confidence=confidence,
            risk_score=risk_score,
            risk_category=risk_category,
            probability_benign=probability_benign,
            probability_malignant=probability_malignant
        )


# Global risk engine instance
risk_engine = RiskEngine()

__all__ = ["RiskEngine", "risk_engine"]