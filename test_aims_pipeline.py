import os
import torch
import numpy as np
from PIL import Image
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mock the backend structure for testing
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend"))

# Mock global settings if not available
try:
    from backend.app.services.model_loader import ModelService
    from backend.app.config import settings
except ImportError:
    # If we are running it inside the repo, just use absolute paths
    sys.path.append(os.getcwd())
    from Aviothic.ai.pvt.ltd.backend.app.services.model_loader import ModelService
    from Aviothic.ai.pvt.ltd.backend.app.config import settings

def test_full_pipeline():
    logger.info("Initializing ModelService (AIMS Portfolio)...")
    service = ModelService(device="cpu") # Use CPU for local test compatibility
    
    # 1. Simulate 4 Views (L-CC, L-MLO, R-CC, R-MLO)
    logger.info("Generating 4-view mock study...")
    mock_views = [
        Image.fromarray(np.random.randint(0, 255, (3000, 2000), dtype=np.uint8))
        for _ in range(4)
    ]
    
    # 2. Run Study Inference
    logger.info("Running multi-view study inference...")
    result = service.predict_study(mock_views)
    
    # 3. Verify Response structure
    logger.info("Verifying response structure...")
    required_keys = ["birads", "cancer_probability", "density", "detections", "risk_category", "explanation"]
    for key in required_keys:
        if key not in result:
            logger.error(f"FAIL: Missing key '{key}'")
            return False
        logger.info(f" - {key}: {result[key]}")
    
    # 4. Success check
    logger.info("PIPELINE TEST PASSED.")
    return True

if __name__ == "__main__":
    test_full_pipeline()
