# Grad-CAM visualization service
import cv2
import numpy as np

class GradCAM:
    def __init__(self, model, layer_name):
        self.model = model
        self.layer_name = layer_name
        
    def compute_heatmap(self, image, pred_index=None):
        """
        Compute Grad-CAM heatmap for interpretability
        """
        # Implementation for Grad-CAM visualization
        # This is a placeholder implementation
        heatmap = np.zeros((image.shape[0], image.shape[1]), dtype=np.float32)
        return heatmap
    
    def overlay_heatmap(self, image, heatmap, alpha=0.4):
        """
        Overlay heatmap on the original image
        """
        # Normalize heatmap
        heatmap = np.uint8(255 * heatmap)
        heatmap = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)
        
        # Combine heatmap with original image
        overlaid_img = cv2.addWeighted(image, alpha, heatmap, 1-alpha, 0)
        return overlaid_img