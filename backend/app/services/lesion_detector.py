import os
import torch
import logging
from PIL import Image
from ultralytics import YOLO
from ..config import settings

logger = logging.getLogger(__name__)

class LesionDetector:
    """Medical Lesion Detector using YOLOv8.
    
    Specialized for identifying specific medical findings:
    - Masses
    - Calcifications
    - Distortions
    """
    
    def __init__(self):
        # In a real scenario, you'd provide weights trained on VinDr-Breast or DDSM
        self.model_path = os.path.join(settings.MODELS_DIR, "yolov8m_mammography.pt")
        self.is_dummy = True
        
        try:
            if os.path.exists(self.model_path):
                self.model = YOLO(self.model_path)
                self.is_dummy = False
                logger.info("YOLO Lesion Detector loaded successfully")
            else:
                # Fallback to standard YOLOv8n for demonstration if medical weights missing
                self.model = YOLO('yolov8n.pt') 
                logger.warning(f"Medical YOLO weights not found at {self.model_path}. Using fallback.")
        except Exception as e:
            logger.error(f"Failed to initialize YOLO: {e}")
            self.model = None

    def detect(self, image_path: str) -> list:
        """Run lesion detection on a mammography image.
        
        Returns:
            List of detections with coordinates and class names.
        """
        if not self.model:
            return []
            
        results = self.model(image_path)
        detections = []
        
        for r in results:
            boxes = r.boxes
            for box in boxes:
                # [x1, y1, x2, y2]
                coords = box.xyxy[0].tolist()
                conf = float(box.conf[0])
                cls = int(box.cls[0])
                name = r.names[cls]
                
                detections.append({
                    "box": coords,
                    "confidence": conf,
                    "class": name,
                    "label": f"{name} ({conf:.2f})"
                })
                
        return detections

# Global instance
lesion_detector = LesionDetector()
