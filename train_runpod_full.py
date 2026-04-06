#!/usr/bin/env python3
"""
Aviothic.ai - Full Production Training Script for RunPod (A100 Optimized)
Source: breast_cancer_ai_FINAL.ipynb
AIMS Study Inspired: Multi-view Ensemble (ViT + DenseNet + EfficientNet)
"""

import os
import time
import json
import argparse
import logging
import random
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader, WeightedRandomSampler
import torchvision.transforms as transforms
import timm
from PIL import Image
from tqdm import tqdm
from sklearn.metrics import roc_auc_score

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Aviothic-RunPod")

# --- MODEL ARCHITECTURE ---

class BreastEnsemble(nn.Module):
    """Multi-view Ensemble Architecture:
    - Inputs: 4 views (L CC, L MLO, R CC, R MLO)
    - Ensemble: ViT + DenseNet + EfficientNet
    - Outputs: BI-RADS classification (num_classes=6)
    """
    def __init__(self, num_classes=2, pretrained=True):
        super(BreastEnsemble, self).__init__()
        
        # 1. Vision Transformer (ViT)
        self.vit = timm.create_model('vit_base_patch16_224', pretrained=pretrained, num_classes=0)
        self.vit_head = nn.Linear(self.vit.num_features * 4, 128)
        
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
            nn.Linear(256, num_classes)
        )

    def forward(self, views):
        """
        Args:
            views: Tensor [Batch, 4, 3, 224, 224] representing 4 standard views
        """
        feats_vit = []
        feats_dense = []
        feats_eff = []
        
        for i in range(4):
            v = views[:, i, :, :, :]
            feats_vit.append(self.vit(v))
            feats_dense.append(self.densenet(v))
            feats_eff.append(self.effnet(v))
            
        v_vit = torch.cat(feats_vit, dim=1)
        v_dense = torch.cat(feats_dense, dim=1)
        v_eff = torch.cat(feats_eff, dim=1)
        
        h_vit = self.vit_head(v_vit)
        h_dense = self.dense_head(v_dense)
        h_eff = self.eff_head(v_eff)
        
        combined = torch.cat([h_vit, h_dense, h_eff], dim=1)
        return self.classifier(combined)

# --- DATASET LOADER ---

class MammographyDataset(Dataset):
    def __init__(self, csv_path, img_dir, transform=None, is_demo=False):
        self.df = pd.read_csv(csv_path) if not is_demo else self._gen_demo_df()
        self.img_dir = img_dir
        self.transform = transform
        self.is_demo = is_demo
        
    def _gen_demo_df(self):
        return pd.DataFrame({
            'path_lcc': ['demo']*200, 'path_lmlo': ['demo']*200,
            'path_rcc': ['demo']*200, 'path_rmlo': ['demo']*200,
            'label': [0, 1]*100
        })

    def __len__(self):
        return len(self.df)

    def _load_img(self, path):
        if self.is_demo:
            return torch.randn(3, 224, 224)
        img = Image.open(path).convert('RGB')
        if self.transform:
            img = self.transform(img)
        return img

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        try:
            view_paths = [row['path_lcc'], row['path_lmlo'], row['path_rcc'], row['path_rmlo']]
            # Note: Expects paths to be absolute or relative to img_dir
            views = torch.stack([self._load_img(os.path.join(self.img_dir, p)) for p in view_paths])
        except Exception as e:
            # Fallback for errors
            views = torch.zeros(4, 3, 224, 224)
            
        label = torch.tensor(int(row['label']), dtype=torch.long)
        return views, label

# --- TRAINING PIPELINE ---

def train(args):
    # Set seeds
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    torch.cuda.manual_seed_all(args.seed)
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    logger.info(f"Using device: {device}")

    # H100 / A100 Hyper-Performance (TF32) - Up to 2-3x Speedup for Matmuls
    if 'cuda' in device.type:
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True
        logger.info("Hopper/Ampere Performance Optimized: TF32 Enabled.")

    # Transforms
    train_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomAffine(degrees=10, translate=(0.05, 0.05), scale=(0.95, 1.05)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    val_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    # Datasets
    train_ds = MammographyDataset(args.train_csv, args.data_dir, transform=train_transform, is_demo=args.demo)
    val_ds = MammographyDataset(args.val_csv, args.data_dir, transform=val_transform, is_demo=args.demo)

    # Imbalance Handling (AIMS Study usually 1.7% cancer rate)
    if not args.demo:
        labels = train_ds.df['label'].values
        class_counts = np.bincount(labels)
        class_weights = 1.0 / class_counts
        sample_weights = class_weights[labels]
        sampler = WeightedRandomSampler(sample_weights, len(sample_weights), replacement=True)
        train_loader = DataLoader(train_ds, batch_size=args.batch_size, sampler=sampler, num_workers=args.workers, pin_memory=True)
    else:
        train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, num_workers=args.workers)
        
    val_loader = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False, num_workers=args.workers)

    # Model, Optimizer, Loss
    model = BreastEnsemble(num_classes=args.num_classes, pretrained=True).to(device)
    
    # PyTorch 2.0+ Compilation (Hopper/H100 Speed Boost)
    if hasattr(torch, 'compile') and not args.demo:
        try:
            logger.info("Initializing Torch Compile (Inductor Backend)... This may take a moment.")
            model = torch.compile(model)
            logger.info("--- ⚡ Compilation Successful ---")
        except Exception as e:
            logger.warning(f"Compilation skipped: {e}")
    
    # Handle Multi-GPU
    if torch.cuda.device_count() > 1:
        logger.info(f"Detected {torch.cuda.device_count()} GPUs. Using DataParallel.")
        model = nn.DataParallel(model)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-5)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)
    
    # AMP Scalar for A100 Speed Boost
    scaler = torch.cuda.amp.GradScaler()

    best_auc = 0.0
    
    logger.info("Starting Training...")
    for epoch in range(args.epochs):
        model.train()
        running_loss = 0.0
        pbar = tqdm(train_loader, desc=f"Epoch {epoch+1}/{args.epochs}")
        
        for batch_idx, (images, labels) in enumerate(pbar):
            images, labels = images.to(device), labels.to(device)
            
            optimizer.zero_grad()
            
            # Use Mixed Precision
            with torch.cuda.amp.autocast():
                outputs = model(images)
                loss = criterion(outputs, labels)
            
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
            
            running_loss += loss.item()
            pbar.set_postfix({'loss': running_loss / (batch_idx + 1)})

        # Validation
        model.eval()
        all_probs = []
        all_labels = []
        with torch.no_grad():
            for images, labels in val_loader:
                images = images.to(device)
                outputs = model(images)
                probs = torch.softmax(outputs, dim=1)[:, 1]
                all_probs.extend(probs.cpu().numpy())
                all_labels.extend(labels.numpy())
        
        epoch_auc = roc_auc_score(all_labels, all_probs)
        logger.info(f"Epoch {epoch+1} Complete. Val AUC: {epoch_auc:.4f} | Loss: {running_loss/len(train_loader):.4f}")
        
        # Save Best Model
        if epoch_auc > best_auc:
            best_auc = epoch_auc
            save_path = os.path.join(args.output_dir, "aviothic_final_AIMS.pt")
            torch.save(model.state_dict() if not isinstance(model, nn.DataParallel) else model.module.state_dict(), save_path)
            logger.info(f"--- 🏆 New Best Model Saved (AUC: {best_auc:.4f}) ---")
            
        scheduler.step()

    logger.info(f"Training Finished. Best AUC: {best_auc:.4f}")

# --- MAIN ---

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Aviothic RunPod Training Script")
    parser.add_argument("--train_csv", type=str, default="data/train.csv")
    parser.add_argument("--val_csv", type=str, default="data/val.csv")
    parser.add_argument("--data_dir", type=str, default="/workspace/data")
    parser.add_argument("--output_dir", type=str, default="/workspace/models")
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--batch_size", type=int, default=64)
    parser.add_argument("--lr", type=float, default=2e-4) # Slightly higher LR for H100/Batch 64
    parser.add_argument("--num_classes", type=int, default=2)
    parser.add_argument("--workers", type=int, default=12) # Use more workers for fast H100
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--demo", action="store_true", help="Run with simulated data")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)
        
    train(args)
