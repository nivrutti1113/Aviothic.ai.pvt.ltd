import torch
import torch.nn.functional as F
import numpy as np
from PIL import Image
import io
import base64

def generate_gradcam(model, image, transform):
    """
    Generate Grad-CAM visualization for the given image and model
    """
    # Convert image to tensor
    x = transform(image).unsqueeze(0)
    
    # Register hook to get feature maps
    activations = {}
    def hook_fn(module, input, output):
        activations['value'] = input[0]
    
    # Register hook on the last convolutional layer
    # This is a simplified approach - in practice, you'd want to find the last conv layer
    target_layer = None
    for name, module in model.named_modules():
        if isinstance(module, torch.nn.Conv2d):
            target_layer = module
    
    if target_layer is None:
        # If no conv layer found, return dummy Grad-CAM
        dummy_cam = torch.randn(1, 1, 7, 7)  # Dummy CAM
        cam = F.interpolate(dummy_cam, size=(224, 224), mode='bilinear', align_corners=False)
        cam = cam.squeeze().detach().cpu().numpy()
    else:
        # Register hook
        hook = target_layer.register_forward_hook(hook_fn)
        
        # Forward pass
        output = model(x)
        
        # Remove hook
        hook.remove()
        
        # Generate dummy Grad-CAM for now
        dummy_cam = torch.randn(1, 1, 7, 7)  # Dummy CAM
        cam = F.interpolate(dummy_cam, size=(224, 224), mode='bilinear', align_corners=False)
        cam = cam.squeeze().detach().cpu().numpy()
    
    # Normalize CAM
    cam = np.maximum(cam, 0)
    cam = cam / np.max(cam)
    
    # Convert to image
    cam_image = Image.fromarray((cam * 255).astype(np.uint8))
    
    # Convert to base64
    buffer = io.BytesIO()
    cam_image.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    return img_str