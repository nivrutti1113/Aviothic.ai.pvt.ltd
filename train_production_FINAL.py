import os
import time
import argparse
import logging
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
logger = logging.getLogger("Aviothic-Production-Final")

# --- RTX 5090 / H100 ARCHITECTURE TUNING ---
torch.backends.cudnn.benchmark = True
torch.backends.cuda.matmul.allow_tf32 = True
torch.backends.cudnn.allow_tf32 = True

# --- PRODUCTION MODEL ARCHITECTURE ---

class EnsembleClassifier(nn.Module):
    def __init__(self, meta_dim=2, num_classes=7, pretrained=True):
        super().__init__()
        # Backbone Ensemble
        self.vit = timm.create_model('vit_base_patch16_224', pretrained=pretrained, num_classes=0)
        self.densenet = timm.create_model('densenet121', pretrained=pretrained, num_classes=0)
        self.effnet = timm.create_model('efficientnet_b3', pretrained=pretrained, num_classes=0)
        
        total_dim = 768 + 1024 + 1536
        self.meta_enc = nn.Sequential(nn.Linear(meta_dim, 64), nn.ReLU(), nn.Linear(64, 128), nn.ReLU())
        
        self.fusion = nn.Sequential(
            nn.Linear(total_dim + 128, 512),
            nn.GELU(),
            nn.Dropout(0.3),
            nn.Linear(512, 256),
            nn.GELU(),
            nn.Linear(256, 128)
        )
        
        # Multi-task Heads
        self.head_birads = nn.Linear(128, num_classes)
        self.head_cancer = nn.Linear(128, 1)

    def forward(self, images, metadata):
        B, V, C, H, W = images.shape
        flat_images = images.view(B * V, C, H, W)
        
        # Extract features across all 4 views
        fv = self.vit(flat_images).view(B, V, -1).mean(1)
        fd = self.densenet(flat_images).view(B, V, -1).mean(1)
        fe = self.effnet(flat_images).view(B, V, -1).mean(1)
        
        # Meta features
        fm = self.meta_enc(metadata)
        
        # Fusion
        combined = torch.cat([fv, fd, fe, fm], dim=1)
        h = self.fusion(combined)
        
        return {
            'birads_logits': self.head_birads(h),
            'cancer_prob': torch.sigmoid(self.head_cancer(h)).squeeze(1),
            'cancer_logit': self.head_cancer(h).squeeze(1)
        }

# --- REAL-WORLD DATASET LOADER ---

class VinDrProductionDataset(Dataset):
    def __init__(self, csv_path, image_dir, transform=None):
        self.df = pd.read_csv(csv_path)
        self.image_dir = image_dir
        self.transform = transform or transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
        # Ensure required columns exist
        required = ['study_id', 'cancer_label', 'birads_score', 'age', 'breast_density']
        for col in required:
            if col not in self.df.columns:
                raise ValueError(f"CRITICAL: Missing required column '{col}' in CSV.")

    def __len__(self):
        return len(self.df)

    def _load_img(self, study_id, view_name):
        # Look for Study_ID/View_Name.png
        # common VinDr naming: {study_id}_{view}.png
        path = os.path.join(self.image_dir, study_id, f"{view_name}.png")
        if not os.path.exists(path):
            path = os.path.join(self.image_dir, f"{study_id}_{view_name}.png") # fallback
            
        if os.path.exists(path):
            img = Image.open(path).convert('RGB')
        else:
            # logger.warning(f"Missing view {view_name} for study {study_id}. Using zero-fill.")
            img = Image.new('RGB', (224, 224), (0, 0, 0))
            
        return self.transform(img)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        study_id = str(row['study_id'])
        
        # Load 4 Standard Views
        views = ['L_CC', 'L_MLO', 'R_CC', 'R_MLO']
        images = torch.stack([self._load_img(study_id, v) for v in views])
        
        # Metadata: Age (normalized) and Density (1-4)
        age = (float(row['age']) - 50) / 20.0
        density = float(row['breast_density']) / 4.0
        metadata = torch.tensor([age, density], dtype=torch.float32)
        
        labels = {
            'cancer': torch.tensor(int(row['cancer_label']), dtype=torch.float32),
            'birads': torch.tensor(int(row['birads_score']) - 1, dtype=torch.long)
        }
        
        return images, labels, metadata

# --- ENGINE ---

def run_production_training(args):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    logger.info(f"🚀 PRODUCTION ENGINE STARTING | DEVICE: {device}")

    # 1. Dataset Initialization
    train_ds = VinDrProductionDataset(args.train_csv, args.image_dir)
    val_ds = VinDrProductionDataset(args.val_csv, args.image_dir)

    # Balanced Sampler for Cancer Imbalance (Crucial for Medical AI)
    labels = train_ds.df['cancer_label'].values.astype(int)
    class_counts = np.bincount(labels)
    class_weights = 1.0 / class_counts
    weights = class_weights[labels]
    sampler = WeightedRandomSampler(weights, len(weights), replacement=True)

    train_loader = DataLoader(train_ds, batch_size=args.batch_size, sampler=sampler, 
                              num_workers=args.workers, pin_memory=True)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False, num_workers=args.workers)

    # 2. Model Setup
    model = EnsembleClassifier(pretrained=True).to(device)
    
    # 5090 JIT Compilation
    try:
        model = torch.compile(model)
        logger.info("✅ Model Compilation Successful.")
    except:
        logger.info("⚠️ Compilation skipped (Host OS issue).")

    # 3. Optimization
    optimizer = optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    criterion_c = nn.BCEWithLogitsLoss()
    criterion_b = nn.CrossEntropyLoss()
    scaler = torch.cuda.amp.GradScaler()

    # 4. Loop
    best_auc = 0.0
    for epoch in range(args.epochs):
        model.train()
        epoch_loss = 0.0
        pbar = tqdm(train_loader, desc=f"Training Epoch {epoch+1}")
        
        for imgs, labels, meta in pbar:
            imgs, c_labels, b_labels, meta = \
                imgs.to(device), labels['cancer'].to(device), labels['birads'].to(device), meta.to(device)

            optimizer.zero_grad(set_to_none=True)
            
            with torch.cuda.amp.autocast():
                out = model(imgs, meta)
                loss_c = criterion_c(out['cancer_logit'], c_labels)
                loss_b = criterion_b(out['birads_logits'], b_labels)
                total_loss = loss_c * 2.0 + loss_b * 0.5
            
            scaler.scale(total_loss).backward()
            scaler.step(optimizer)
            scaler.update()
            
            epoch_loss += total_loss.item()
            pbar.set_postfix({'loss': epoch_loss/len(pbar)})

        # Validation
        model.eval()
        val_probs, val_labels = [], []
        with torch.no_grad():
            for imgs, labels, meta in val_loader:
                imgs, meta = imgs.to(device), meta.to(device)
                with torch.cuda.amp.autocast():
                    out = model(imgs, meta)
                val_probs.extend(out['cancer_prob'].cpu().numpy())
                val_labels.extend(labels['cancer'].numpy())
        
        auc = roc_auc_score(val_labels, val_probs)
        logger.info(f"📊 Validation Complete | AUC: {auc:.4f}")

        if auc > best_auc:
            best_auc = auc
            save_path = os.path.join(args.output_dir, "production_weights_v2.pt")
            sd = model.state_dict() if not hasattr(model, '_orig_mod') else model._orig_mod.state_dict()
            torch.save(sd, save_path)
            logger.info(f"🏆 Best Weights Saved to {save_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--train_csv", type=str, required=True)
    parser.add_argument("--val_csv", type=str, required=True)
    parser.add_argument("--image_dir", type=str, required=True)
    parser.add_argument("--output_dir", type=str, default="./models")
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--epochs", type=int, default=60)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--workers", type=int, default=12)
    
    args = parser.parse_args()
    if not os.path.exists(args.output_dir): os.makedirs(args.output_dir)
    run_production_training(args)
