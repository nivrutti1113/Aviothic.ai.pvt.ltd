#!/usr/bin/env python3
"""training/trainer.py
Contains a simple run_training_loop and helpers for model build/load.
"""
import os, time, json
import torch, numpy as np
from sklearn.metrics import roc_auc_score
from torch.utils.data import DataLoader

def build_model(num_classes=2, pretrained=True):
    from torchvision import models
    model = models.efficientnet_b0(pretrained=pretrained)
    num_ftrs = model.classifier[1].in_features
    import torch.nn as nn
    model.classifier[1] = nn.Linear(num_ftrs, num_classes)
    return model

class BreastEnsemble(torch.nn.Module):
    """Multi-view Ensemble Architecture:
    - Inputs: 4 views (L CC, L MLO, R CC, R MLO)
    - Ensemble: ViT + DenseNet + EfficientNet
    - Outputs: BI-RADS classification (num_classes=6)
    """
    def __init__(self, num_classes=6, pretrained=True):
        super(BreastEnsemble, self).__init__()
        import timm
        import torch.nn as nn
        
        # 1. Vision Transformer (ViT)
        self.vit = timm.create_model('vit_base_patch16_224', pretrained=pretrained, num_classes=0)
        self.vit_head = nn.Linear(self.vit.num_features * 4, 128) # 4 views
        
        # 2. DenseNet
        self.densenet = timm.create_model('densenet121', pretrained=pretrained, num_classes=0)
        self.dense_head = nn.Linear(self.densenet.num_features * 4, 128)
        
        # 3. EfficientNet
        self.effnet = timm.create_model('efficientnet_b0', pretrained=pretrained, num_classes=0)
        self.eff_head = nn.Linear(self.effnet.num_features * 4, 128)
        
        # Merge Ensemble
        self.classifier = nn.Sequential(
            nn.Linear(128 * 3, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, num_classes) # Final BI-RADS prediction
        )

    def forward(self, views):
        """Forward pass for multi-view ensemble.
        
        Args:
            views: List of 4 tensors [B, 3, 224, 224] for L-CC, L-MLO, R-CC, R-MLO
        """
        feats_vit = []
        feats_dense = []
        feats_eff = []
        
        for v in views:
            feats_vit.append(self.vit(v))
            feats_dense.append(self.densenet(v))
            feats_eff.append(self.effnet(v))
            
        # Cat 4 views per case
        v_vit = torch.cat(feats_vit, dim=1)
        v_dense = torch.cat(feats_dense, dim=1)
        v_eff = torch.cat(feats_eff, dim=1)
        
        # Pass through individual heads
        h_vit = self.vit_head(v_vit)
        h_dense = self.dense_head(v_dense)
        h_eff = self.eff_head(v_eff)
        
        # Combine Ensemble
        combined = torch.cat([h_vit, h_dense, h_eff], dim=1)
        return self.classifier(combined)

def build_ensemble(num_classes=6, pretrained=True):
    return BreastEnsemble(num_classes=num_classes, pretrained=pretrained)

def load_model_for_eval(path, device='cpu'):
    # expects a full state_dict or model saved via torch.save(model.state_dict())
    map_location = torch.device(device)
    try:
        sd = torch.load(path, map_location=map_location)
        # if sd is state_dict, need model architecture to load; user should ensure consistency
        model = build_model(pretrained=False)
        model.load_state_dict(sd)
        model.eval()
        return model
    except Exception:
        # try load entire model
        model = torch.load(path, map_location=map_location)
        model.eval()
        return model

def evaluate_model(model, loader, device='cpu'):
    model.eval()
    ys = []
    ps = []
    with torch.no_grad():
        for xb, yb in loader:
            xb = xb.to(device)
            logits = model(xb)
            probs = torch.softmax(logits, dim=1)[:,1].cpu().numpy()
            ps.extend(probs.tolist())
            ys.extend(yb.numpy().tolist())
    auc = None
    try:
        auc = roc_auc_score(ys, ps)
    except Exception:
        auc = 0.0
    return {'auc': auc, 'preds': ps, 'trues': ys}

def run_training_loop(model, train_dataset, val_dataset, output_dir='/tmp/model_out',
                      epochs=10, batch_size=16, lr=1e-4, device='cpu', patience=3):
    os.makedirs(output_dir, exist_ok=True)
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=2)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=2)
    device = torch.device(device)
    model = model.to(device)
    import torch.nn as nn, torch.optim as optim
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=lr)
    best_auc = -1.0
    best_path = None
    epochs_no_improve = 0
    
    for epoch in range(epochs):
        # Training phase
        model.train()
        train_loss = 0.0
        for xb, yb in train_loader:
            xb, yb = xb.to(device), yb.to(device)
            optimizer.zero_grad()
            logits = model(xb)
            loss = criterion(logits, yb)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()
        
        # Validation phase
        val_metrics = evaluate_model(model, val_loader, device)
        val_auc = val_metrics['auc']
        
        print(f"Epoch {epoch+1}/{epochs}, Train Loss: {train_loss/len(train_loader):.4f}, Val AUC: {val_auc:.4f}")
        
        # Save best model
        if val_auc > best_auc:
            best_auc = val_auc
            best_path = os.path.join(output_dir, f"best_model_epoch_{epoch+1}.pth")
            torch.save(model.state_dict(), best_path)
            epochs_no_improve = 0
        else:
            epochs_no_improve += 1
            
        # Early stopping
        if epochs_no_improve >= patience:
            print(f"Early stopping at epoch {epoch+1}")
            break
    
    if best_path is None:
        best_path = os.path.join(output_dir, "final_model.pth")
        torch.save(model.state_dict(), best_path)
        
    return best_path, {'best_auc': best_auc}