import cv2
import numpy as np
from PIL import Image
import torch
from torchvision import transforms

class CLAHEPipeline:
    """Medical Preprocessing with CLAHE and Automated Breast-Region Cropping."""

    VENDOR_CLAHE = {
        'Hologic': {'clip_limit': 2.0, 'tile_grid_size': (8, 8)},
        'GE': {'clip_limit': 1.5, 'tile_grid_size': (8, 8)},
        'Siemens': {'clip_limit': 2.5, 'tile_grid_size': (8, 8)},
        'default': {'clip_limit': 2.0, 'tile_grid_size': (8, 8)}
    }

    def __init__(self, vendor='Hologic', target_size=(224, 224)):
        p = self.VENDOR_CLAHE.get(vendor, self.VENDOR_CLAHE['default'])
        self.clahe = cv2.createCLAHE(clipLimit=p['clip_limit'], tileGridSize=p['tile_grid_size'])
        self.target_size = target_size

    def _normalize_16bit(self, img):
        img = img.astype(np.float32)
        p2, p98 = np.percentile(img, [2, 98])
        return np.clip((img - p2) / (p98 - p2 + 1e-8), 0, 1)

    def _crop_breast(self, img, offset_px=100):
        """Automated breast-region crop using intensity scan."""
        h, w = img.shape[:2]
        strip_h = h // 5
        y_start = h // 2 - strip_h // 2
        y_end = y_start + strip_h
        threshold = 30.0 / 255.0

        # Boundary check
        left_mean = img[y_start:y_end, :50].mean()
        right_mean = img[y_start:y_end, -50:].mean()

        if left_mean < right_mean: # Breast is on the right
            for col in range(w):
                if img[y_start:y_end, col].mean() > threshold:
                    cropx_min = max(0, col - offset_px)
                    cropx_max = w
                    break
            else: cropx_min, cropx_max = 0, w
        else: # Breast is on the left
            for col in range(w - 1, -1, -1):
                if img[y_start:y_end, col].mean() > threshold:
                    cropx_min = 0
                    cropx_max = min(w, col + offset_px)
                    break
            else: cropx_min, cropx_max = 0, w
        
        return img[:, cropx_min:cropx_max]

    def _apply_clahe(self, img):
        img_u8 = (img * 255).astype(np.uint8)
        if img_u8.ndim == 2:
            return self.clahe.apply(img_u8).astype(np.float32) / 255.0
        else:
            yuv = cv2.cvtColor(img_u8, cv2.COLOR_BGR2YUV)
            yuv[:, :, 0] = self.clahe.apply(yuv[:, :, 0])
            return cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR).astype(np.float32) / 255.0

    def process(self, image_np: np.ndarray) -> torch.Tensor:
        """Full pipeline: Norm -> Crop -> CLAHE -> Resize -> ToTensor."""
        if image_np.dtype == np.uint16:
            img = self._normalize_16bit(image_np)
        else:
            img = image_np.astype(np.float32) / 255.0 if image_np.max() > 1 else image_np
        
        img = self._crop_breast(img)
        img = self._apply_clahe(img)
        
        # Resize to target
        img = cv2.resize(img, (self.target_size[1], self.target_size[0]))
        
        # Norm with ImageNet standards (as common in timm models)
        img_3ch = np.stack([img, img, img], axis=0)
        t = torch.from_numpy(img_3ch).float()
        mean = torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1)
        std = torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1)
        return (t - mean) / std

def dicom_to_numpy(pydicom_ds):
    """Convert valid DICOM to numpy."""
    try:
        return pydicom_ds.pixel_array
    except Exception:
        return None
