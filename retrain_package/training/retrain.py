#!/usr/bin/env python3
"""training/retrain.py
Simple retrain driver that uses ClinicalDataset and trainer.run_training_loop.
Logs to MLflow if MLFLOW_TRACKING_URI is set.
"""
import argparse, os, logging, json
from pathlib import Path

import torch

try:
    import mlflow
except Exception:
    mlflow = None

from dataset import ClinicalDataset
from trainer import run_training_loop, build_model

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('retrain')

def main(args):
    run_id = args.run_id or f"run_{os.getpid()}"
    local_data = args.data_dir or f"/tmp/data/{run_id}"
    os.makedirs(local_data, exist_ok=True)
    logger.info("Preparing dataset from %s", local_data)
    ds = ClinicalDataset(local_data, image_size=args.img_size)
    train_ds, val_ds = ds.train_val_split(val_frac=args.val_frac, seed=args.seed)
    logger.info('Train size: %d, Val size: %d', len(train_ds), len(val_ds))

    model = build_model(num_classes=args.num_classes, pretrained=args.pretrained)
    device = torch.device(args.device)
    best_path, val_metrics = run_training_loop(
        model=model,
        train_dataset=train_ds,
        val_dataset=val_ds,
        output_dir=args.output_dir,
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        device=device,
        patience=args.patience
    )

    logger.info('Best model saved to %s', best_path)
    # Log to MLflow if configured
    if mlflow is not None and os.environ.get('MLFLOW_TRACKING_URI'):
        mlflow.set_tracking_uri(os.environ.get('MLFLOW_TRACKING_URI'))
        with mlflow.start_run(run_name=run_id):
            mlflow.log_params({
                'epochs': args.epochs, 'batch_size': args.batch_size, 'lr': args.lr
            })
            for k,v in val_metrics.items():
                mlflow.log_metric(k, float(v))
            mlflow.log_artifact(best_path, artifact_path='model')
            mlflow.log_param('local_data', local_data)
    print(json.dumps({'best_model': best_path, 'val_metrics': val_metrics}))

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--run_id', default=None)
    p.add_argument('--data_dir', default=None, help='Local dataset dir (overrides s3)')
    p.add_argument('--output_dir', default='/tmp/aviothic_model')
    p.add_argument('--epochs', type=int, default=10)
    p.add_argument('--batch_size', type=int, default=16)
    p.add_argument('--lr', type=float, default=1e-4)
    p.add_argument('--img_size', type=int, default=224)
    p.add_argument('--val_frac', type=float, default=0.2)
    p.add_argument('--device', default='cuda' if torch.cuda.is_available() else 'cpu')
    p.add_argument('--num_classes', type=int, default=2)
    p.add_argument('--pretrained', action='store_true')
    p.add_argument('--patience', type=int, default=3)
    p.add_argument('--seed', type=int, default=42)
    args = p.parse_args()
    main(args)