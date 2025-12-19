#!/usr/bin/env python3
"""training/dataset.py
Minimal ClinicalDataset implementation:
- Supports folder layout: data/<class_label>/*.png (or jpg)
- Optionally reads DICOM (.dcm) using pydicom
- Provides train/val split and PyTorch dataloader helpers
"""
import os, glob, random
from PIL import Image
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader, Subset
try:
    import pydicom
except Exception:
    pydicom = None

class ClinicalDataset(Dataset):
    def __init__(self, root_dir, image_size=224, mode='train', transform=None):
        self.root = root_dir
        self.image_size = image_size
        self.mode = mode
        self.transform = transform
        self.samples = []
        # expect structure root/class_label/*.png
        for label_dir in sorted(os.listdir(root_dir)):
            p = os.path.join(root_dir, label_dir)
            if not os.path.isdir(p):
                continue
            for img_path in glob.glob(os.path.join(p, '*')):
                if img_path.lower().endswith(('.png','.jpg','.jpeg','.dcm')):
                    label = 1 if label_dir.lower() in ('malignant','malign','1','pos','positive') else 0
                    self.samples.append((img_path, label))
        if len(self.samples)==0:
            raise RuntimeError(f'No image files found under {root_dir}')
        random.shuffle(self.samples)

    def __len__(self):
        return len(self.samples)

    def read_image(self, path):
        if path.lower().endswith('.dcm') and pydicom is not None:
            ds = pydicom.dcmread(path)
            arr = ds.pixel_array
            img = Image.fromarray(arr).convert('RGB')
        else:
            img = Image.open(path).convert('RGB')
        img = img.resize((self.image_size, self.image_size))
        return img

    def __getitem__(self, idx):
        path, label = self.samples[idx]
        img = self.read_image(path)
        img_arr = np.array(img).astype('float32')/255.0
        # HWC -> CHW
        img_tensor = torch.tensor(img_arr).permute(2,0,1)
        return img_tensor, torch.tensor(label, dtype=torch.long)

    def train_val_split(self, val_frac=0.2, seed=42):
        n = len(self.samples)
        idx = list(range(n))
        random.Random(seed).shuffle(idx)
        cut = int(n*(1-val_frac))
        train_idx = idx[:cut]
        val_idx = idx[cut:]
        train_ds = Subset(self, train_idx)
        val_ds = Subset(self, val_idx)
        return train_ds, val_ds

    def as_dataloader(self, batch_size=16, shuffle=False, num_workers=0):
        return DataLoader(self, batch_size=batch_size, shuffle=shuffle, num_workers=num_workers)