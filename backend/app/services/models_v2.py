import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.models as tv_models
import numpy as np

# Helper for PyTorch 2.x safe model creation
def _resnet50(pretrained=False):
    try:
        from torchvision.models import ResNet50_Weights
        w = ResNet50_Weights.DEFAULT if pretrained else None
        return tv_models.resnet50(weights=w)
    except ImportError:
        return tv_models.resnet50(pretrained=pretrained)

def _densenet121(pretrained=False):
    try:
        from torchvision.models import DenseNet121_Weights
        w = DenseNet121_Weights.DEFAULT if pretrained else None
        return tv_models.densenet121(weights=w)
    except ImportError:
        return tv_models.densenet121(pretrained=pretrained)

class DensityClassifier(nn.Module):
    """BIRADS Density Classifier (EfficientNet-B3 focused)."""
    def __init__(self, pretrained=False):
        super().__init__()
        import timm
        self.backbone = timm.create_model('efficientnet_b3', pretrained=pretrained, num_classes=4)
    
    def forward(self, x):
        # Expects [B, 4, 3, 224, 224] - multi-view
        B, V, C, H, W = x.shape
        # Simple mean-pooling over views for density
        logits = self.backbone(x.view(B*V, C, H, W)).view(B, V, -1).mean(1)
        return logits

class LesionClassifier(nn.Module):
    """Multi-task Lesion Attribute Classifier."""
    def __init__(self, pretrained=False):
        super().__init__()
        base = _resnet50(pretrained)
        fd = base.fc.in_features
        self.backbone = nn.Sequential(*list(base.children())[:-1], nn.Flatten())
        self.head_lesion_type = nn.Linear(fd, 5) # None, Mass, Calc, Dist, Asym
        self.head_malignancy = nn.Linear(fd, 1)
    
    def forward(self, x):
        feat = self.backbone(x)
        return {
            'lesion_type': self.head_lesion_type(feat),
            'malignancy': torch.sigmoid(self.head_malignancy(feat))
        }

class CalcificationPatchClassifier(nn.Module):
    """Lightweight Patch Classifier for Microcalcifications."""
    def __init__(self, pretrained=False):
        super().__init__()
        import timm
        self.backbone = timm.create_model('efficientnet_b0', pretrained=pretrained, num_classes=1)
    
    def forward(self, x):
        return torch.sigmoid(self.backbone(x))

class EnsembleClassifier(nn.Module):
    """Main BI-RADS and Cancer Risk Ensemble."""
    def __init__(self, pretrained=False):
        super().__init__()
        import timm
        # ViT + DenseNet121 + EffNetB3
        self.vit = timm.create_model('vit_base_patch16_224', pretrained=pretrained, num_classes=0)
        self.densenet = _densenet121(pretrained)
        self.densenet = nn.Sequential(*list(self.densenet.children())[:-1], nn.Flatten())
        self.effnet = timm.create_model('efficientnet_b3', pretrained=pretrained, num_classes=0)
        
        total_dim = 768 + 1024 + 1536
        self.fusion = nn.Sequential(
            nn.Linear(total_dim, 512),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(512, 7) # BI-RADS 0-6
        )
        self.cancer_head = nn.Linear(512, 1)

    def forward(self, images):
        # images: [B, V, 3, 224, 224]
        B, V, C, H, W = images.shape
        flat = images.view(B*V, C, H, W)
        
        fv = self.vit(flat).view(B, V, -1).mean(1)
        fd = self.densenet(flat).view(B, V, -1).mean(1)
        fe = self.effnet(flat).view(B, V, -1).mean(1)
        
        combined = torch.cat([fv, fd, fe], dim=1)
        h = self.fusion[0:3](combined)
        birads = self.fusion[3:](h)
        cancer = torch.sigmoid(self.cancer_head(h))
        
        return birads, cancer
