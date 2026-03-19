import os
import uuid
import logging
from typing import Optional

import numpy as np
import cv2
import torch
import torch.nn.functional as F
from PIL import Image

from ..config import settings

logger = logging.getLogger(__name__)


def _ensure_dirs():
    """Ensure required directories exist for Grad-CAM storage."""
    os.makedirs(settings.GRADCAM_DIR, exist_ok=True)
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)


def generate_gradcam(model: torch.nn.Module, 
                     input_tensor: torch.Tensor, 
                     orig_image: Image.Image, 
                     target_class: Optional[int] = None) -> str:
    """Production-ready Grad-CAM implementation with medical audit compliance.
    
    Computes class-specific Grad-CAM heatmap and overlays it on the original image.
    Medical audit friendly with clear error handling and dummy model detection.
    
    Args:
        model: PyTorch model in eval mode
        input_tensor: Preprocessed input tensor [1, C, H, W]
        orig_image: Original PIL image for overlay
        target_class: Class to generate heatmap for. If None, uses predicted class
    
    Returns:
        Filesystem path to saved Grad-CAM overlay image
        
    DUMMY MODEL HANDLING: If no Conv2D layers found, saves clearly marked
    fallback image indicating dummy model usage.
    
    REAL GRAD-CAM: Uses proper forward/backward hooks for gradient computation
    and class-specific activation mapping.
    """
    _ensure_dirs()
    
    # Ensure model and input are on same device
    device = next(model.parameters()).device if any(True for _ in model.parameters()) else torch.device("cpu")
    input_tensor = input_tensor.to(device)
    
    # Find the last Conv2d layer for Grad-CAM
    target_layer = None
    conv_layers = []
    
    for name, module in model.named_modules():
        if isinstance(module, torch.nn.Conv2d):
            target_layer = module
            conv_layers.append((name, module))
            logger.debug(f"Found Conv2d layer: {name}")
    
    # DUMMY MODEL FALLBACK: No convolutional layers found
    if target_layer is None:
        logger.warning("DUMMY MODEL DETECTED: No Conv2d layers found for Grad-CAM")
        return _save_dummy_gradcam(orig_image, "DUMMY_GRADCAM_NO_CONV_LAYERS")
    
    logger.debug(f"Using Conv2d layer for Grad-CAM: {conv_layers[-1][0] if conv_layers else 'unknown'}")
    
    # Setup hooks for gradient capture
    activations = {}
    gradients = {}
    
    def forward_hook(module, inp, out):
        """Capture forward pass activations."""
        activations['value'] = out.detach()
        logger.debug(f"Forward hook captured activation shape: {out.shape}")
    
    def backward_hook(module, grad_in, grad_out):
        """Capture backward pass gradients."""
        gradients['value'] = grad_out[0].detach()
        logger.debug(f"Backward hook captured gradient shape: {grad_out[0].shape}")
    
    # Register hooks
    fh = target_layer.register_forward_hook(forward_hook)
    bh = target_layer.register_full_backward_hook(backward_hook)
    
    try:
        # Zero gradients and run forward pass
        model.zero_grad()
        output = model(input_tensor)
        
        # Determine target class for heatmap
        if target_class is None:
            target_class = int(output.argmax(dim=1).item())
            logger.debug(f"Using predicted class {target_class} for Grad-CAM")
        else:
            logger.debug(f"Using specified class {target_class} for Grad-CAM")
        
        # Compute gradients for target class
        score = output[0, target_class]
        score.backward(retain_graph=False)
        logger.debug("Gradient computation completed")
        
    finally:
        # Always remove hooks to prevent memory leaks
        fh.remove()
        bh.remove()
        logger.debug("Hooks removed")
    
    # Extract captured activations and gradients
    acts = activations.get('value')  # [1, C, H, W]
    grads = gradients.get('value')   # [1, C, H, W]
    
    if acts is None or grads is None:
        logger.error("Failed to capture activations or gradients")
        return _save_dummy_gradcam(orig_image, "GRADCAM_HOOK_CAPTURE_FAILED")
    
    # Compute Grad-CAM: Global Average Pooling of gradients -> channel weights
    weights = grads.mean(dim=(2, 3), keepdim=True)  # [1, C, 1, 1]
    logger.debug(f"Computed weights shape: {weights.shape}")
    
    # Weighted combination of activations
    cam = (weights * acts).sum(dim=1, keepdim=True)  # [1, 1, H, W]
    cam = F.relu(cam)  # Apply ReLU to highlight positive contributions
    
    # Process CAM to numpy array
    cam = cam.squeeze(0).squeeze(0).cpu().numpy()
    cam = cam - cam.min()
    if cam.max() != 0:
        cam = cam / cam.max()
    
    # Resize CAM to original image dimensions
    orig_w, orig_h = orig_image.size
    cam_resized = cv2.resize(cam, (orig_w, orig_h))
    logger.debug(f"CAM resized to: {cam_resized.shape}")
    
    # Create heatmap visualization
    heatmap = np.uint8(255 * cam_resized)
    heatmap = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)
    
    # Overlay heatmap on original image
    img_np = cv2.cvtColor(np.array(orig_image.convert('RGB')), cv2.COLOR_RGB2BGR)
    overlay = cv2.addWeighted(img_np, 0.6, heatmap, 0.4, 0)
    
    # Save result with unique filename
    filename = f"gradcam_{uuid.uuid4().hex}.png"
    save_path = os.path.join(settings.GRADCAM_DIR, filename)
    cv2.imwrite(save_path, overlay)
    
    logger.info(f"Grad-CAM saved to: {save_path}")
    return save_path


def _save_dummy_gradcam(orig_image: Image.Image, message: str) -> str:
    """Save dummy Grad-CAM image with clear error message.
    
    Args:
        orig_image: Original image
        message: Error message to display on image
        
    Returns:
        Path to saved dummy image
    """
    filename = f"gradcam_dummy_{uuid.uuid4().hex}.png"
    save_path = os.path.join(settings.GRADCAM_DIR, filename)
    
    img_np = cv2.cvtColor(np.array(orig_image.convert('RGB')), cv2.COLOR_RGB2BGR)
    cv2.putText(img_np, message, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
    cv2.putText(img_np, "DUMMY_MODEL_NOT_FOR_MEDICAL_USE", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 1)
    
    cv2.imwrite(save_path, img_np)
    logger.warning(f"Dummy Grad-CAM saved: {save_path} with message: {message}")
    return save_path


__all__ = ["generate_gradcam"]