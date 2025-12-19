#!/usr/bin/env python3
"""training/validate.py
Validate a saved model on a provided dataset and enforce thresholds.
"""
import argparse, os, json, sys
import torch
import numpy as np
from sklearn.metrics import roc_auc_score, confusion_matrix, accuracy_score
from dataset import ClinicalDataset
from trainer import load_model_for_eval

def main(args):
    model_path = args.model_path
    data_dir = args.data_dir
    ds = ClinicalDataset(data_dir, image_size=args.img_size, mode='infer')
    loader = ds.as_dataloader(batch_size=args.batch_size)
    model = load_model_for_eval(model_path, device=args.device)
    preds = []
    trues = []
    for imgs, labels in loader:
        imgs = imgs.to(args.device)
        with torch.no_grad():
            logits = model(imgs)
            probs = torch.softmax(logits, dim=1)[:,1].cpu().numpy()
            preds.extend(probs.tolist())
            trues.extend(labels.numpy().tolist())
    auc = roc_auc_score(trues, preds)
    acc = accuracy_score(trues, [1 if p>0.5 else 0 for p in preds])
    print(json.dumps({'auc':auc, 'accuracy':acc}))
    # threshold check
    if auc < args.min_auc:
        print(f"AUC {auc} below threshold {args.min_auc}")
        sys.exit(2)
    print('Validation passed.')
    sys.exit(0)

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--model_path', required=True)
    p.add_argument('--data_dir', required=True)
    p.add_argument('--img_size', type=int, default=224)
    p.add_argument('--batch_size', type=int, default=16)
    p.add_argument('--device', default='cuda' if torch.cuda.is_available() else 'cpu')
    p.add_argument('--min_auc', type=float, default=0.95)
    args = p.parse_args()
    main(args)