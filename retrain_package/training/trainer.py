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