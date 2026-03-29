import torch
import torch.nn.functional as F
from PIL import Image
import numpy as np
import os
import logging
from ..config import settings
from .preprocessing import CLAHEPipeline
from .models_v2 import (
    EnsembleClassifier, 
    DensityClassifier, 
    LesionClassifier, 
    CalcificationPatchClassifier
)

logger = logging.getLogger(__name__)

# YOLO loader if available
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False

class PatchTiler:
    def __init__(self, patch_size=256, stride=192):
        self.patch_size = patch_size
        self.stride = stride
    
    def extract(self, img):
        h, w = img.shape[:2]
        patches = []
        for r in range(0, h - self.patch_size + 1, self.stride):
            for c in range(0, w - self.patch_size + 1, self.stride):
                patch = img[r:r+self.patch_size, c:c+self.patch_size]
                patches.append({'patch': patch, 'row': r, 'col': c})
        return patches

class ModelService:
    """Production Multi-Stage AI Screening Pipeline inspired by AIMS Study."""

    def __init__(self, device: str = None):
        self.device = torch.device(device or settings.DEVICE)
        self.is_dummy_model = False
        
        # 1. Initialize Preprocessing
        self.preprocessor = CLAHEPipeline()
        self.tiler = PatchTiler()
        
        # 2. Load Stages
        self._load_all_models()
        logger.info(f"AIMS Screening Pipeline initialized on {self.device}")

    def _load_all_models(self):
        """Orchestrate loading of all 5 specialized models."""
        try:
            # 2.1 Ensemble (Main Scoring)
            self.ensemble = EnsembleClassifier(pretrained=False).to(self.device)
            if os.path.exists(settings.MODEL_PATH):
                self.ensemble.load_state_dict(torch.load(settings.MODEL_PATH, map_location=self.device))
                logger.info("Ensemble weights (v2) loaded.")
            else:
                self.is_dummy_model = True
                logger.warning("Ensemble weights not found. Using stub modes.")

            # 2.2 Density Classifier
            self.density_model = DensityClassifier(pretrained=False).to(self.device)
            if os.path.exists(settings.DENSITY_MODEL_PATH):
                self.density_model.load_state_dict(torch.load(settings.DENSITY_MODEL_PATH, map_location=self.device))
                logger.info("Density model weights loaded.")

            # 2.3 Lesion Classifier (Micro-tasks)
            self.lesion_model = LesionClassifier(pretrained=False).to(self.device)
            if os.path.exists(settings.LESION_MODEL_PATH):
                self.lesion_model.load_state_dict(torch.load(settings.LESION_MODEL_PATH, map_location=self.device))
                logger.info("Lesion model weights loaded.")

            # 2.4 Patch Classifier (Calcs)
            self.calc_model = CalcificationPatchClassifier(pretrained=False).to(self.device)
            if os.path.exists(settings.CALC_PATCH_MODEL_PATH):
                self.calc_model.load_state_dict(torch.load(settings.CALC_PATCH_MODEL_PATH, map_location=self.device))
                logger.info("Patch classifier weights loaded.")

            # 2.5 YOLO (Localization)
            if YOLO_AVAILABLE:
                if os.path.exists(settings.YOLO_MODEL_PATH):
                    self.yolo = YOLO(settings.YOLO_MODEL_PATH)
                    logger.info("YOLOv8 weights loaded.")
                else:
                    self.yolo = None
                    logger.warning("YOLO weights missing.")
            else:
                self.yolo = None

        except Exception as e:
            logger.error(f"Failed to load full AIMS pipeline: {e}")
            self.is_dummy_model = True

    def preprocess(self, pil_image: Image.Image) -> tuple[torch.Tensor, np.ndarray]:
        """Convert PIL to Tensor using CLAHE Pipeline and return np for YOLO."""
        img_np = np.array(pil_image.convert('L'))
        # Ensure we have a valid 16-bit-like range if possible, or 8-bit
        tensor = self.preprocessor.process(img_np).unsqueeze(0).to(self.device)
        return tensor, img_np

    def predict_study(self, study_views: list[Image.Image]) -> dict:
        """Complete Case-Level Screening Inferences."""
        # 1. Preprocess all 4 views (CC_L, MLO_L, CC_R, MLO_R)
        view_tensors = []
        full_np_images = []
        for img in study_views[:4]:
            t, n = self.preprocess(img)
            view_tensors.append(t)
            full_np_images.append(n)
        
        # Ensure exactly 4 views for ensemble
        while len(view_tensors) < 4:
            dummy = torch.zeros_like(view_tensors[0])
            view_tensors.append(dummy)
            full_np_images.append(None)
            
        study_tensor = torch.stack(view_tensors, dim=1) # [1, 4, 3, 224, 224]

        with torch.no_grad():
            # 2. Main Risk & BI-RADS
            birads_logits, cancer_prob = self.ensemble(study_tensor)
            birads_pred = int(torch.argmax(birads_logits, dim=1).item())
            cancer_score = float(cancer_prob.item())
            
            # 3. Density Classification
            density_logits = self.density_model(study_tensor)
            density_pred = int(torch.argmax(density_logits, dim=1).item())
            density_label = ["A", "B", "C", "D"][density_pred]
            
            # 4. Localization (YOLO) on all views
            all_detections = []
            if self.yolo:
                for idx, img_np in enumerate(full_np_images):
                    if img_np is not None:
                        res = self.yolo(img_np, verbose=False)
                        for r in res:
                            for box in r.boxes:
                                all_detections.append({
                                    'view': idx,
                                    'bbox': box.xyxy[0].tolist(),
                                    'conf': float(box.conf[0].item()),
                                    'class': r.names[int(box.cls[0].item())]
                                })

            # 5. Patch-based Calcification Check (First view for demo speed)
            calc_clusters = []
            if full_np_images[0] is not None:
                patches = self.tiler.extract(full_np_images[0])
                # In production, batch this
                for p_info in patches[:10]: # Limit for performance
                    p_tensor = torch.from_numpy(np.stack([p_info['patch']]*3, axis=0)).float().unsqueeze(0).to(self.device)
                    p_prob = float(self.calc_model(p_tensor).item())
                    if p_prob > 0.5:
                        calc_clusters.append({'row': p_info['row'], 'col': p_info['col'], 'prob': p_prob})

            return {
                "birads": birads_pred,
                "cancer_probability": cancer_score,
                "density": density_label,
                "detections": all_detections,
                "calc_clusters": calc_clusters,
                "risk_category": "High" if cancer_score > 0.065 else "Normal", # AIMS threshold
                "explanation": f"Advanced AIMS Modular Pipeline Analysis: BI-RADS {birads_pred} detected with density grade {density_label}."
            }

    def predict(self, input_tensor: torch.Tensor, image_path: str = None) -> tuple:
        """Legacy compatibility wrapper."""
        # Wrap single tensor into 4 views for the multi-view architecture
        views = [input_tensor.cpu()] * 4
        # Convert back to PIL for consistency with predict_study
        pil_images = [Image.fromarray((v.squeeze(0).permute(1,2,0).numpy()*255).astype(np.uint8)) for v in views]
        res = self.predict_study(pil_images)
        
        # Return tuple to match old signature if needed, or update consumers
        # Old sig: predicted_class, prob_list, confidence, risk_score, explanation, birads, lesion, density, detections
        # Note: This is becoming messy, better to update the consumer (API route)
        return (
            res['birads'], 
            [0.0]*7, # prob_list stub
            res['cancer_probability'], 
            int(res['cancer_probability']*100), 
            res['explanation'], 
            str(res['birads']), 
            res['detections'][0]['class'] if res['detections'] else "None",
            res['density'], 
            res['detections']
        )

    def get_model_info(self) -> dict:
        return {
            "version": settings.MODEL_VERSION,
            "stages": ["Ensemble", "Density", "Lesion", "YOLOv8", "Calc-Patch"],
            "preprocessing": "AIMS-style CLAHE + Cropping",
            "device": str(self.device),
            "is_dummy_model": self.is_dummy_model
        }

__all__ = ["ModelService"]