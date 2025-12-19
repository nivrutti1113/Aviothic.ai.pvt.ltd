#!/usr/bin/env python3
"""training/tune_optuna.py
Hyperparameter tuning using Optuna with ClinicalDataset and trainer.
"""
import argparse
import optuna
import torch
import json
import os
from dataset import ClinicalDataset
from trainer import run_training_loop, build_model

def objective(trial, args):
    # Suggest hyperparameters
    lr = trial.suggest_float("lr", 1e-5, 1e-1, log=True)
    batch_size = trial.suggest_categorical("batch_size", [8, 16, 32, 64])
    epochs = trial.suggest_int("epochs", 5, 50)
    
    # Prepare dataset
    ds = ClinicalDataset(args.data_dir, image_size=args.img_size)
    train_ds, val_ds = ds.train_val_split(val_frac=args.val_frac, seed=args.seed)
    
    # Build model
    model = build_model(num_classes=args.num_classes, pretrained=args.pretrained)
    device = torch.device(args.device)
    
    # Run training
    output_dir = os.path.join(args.output_dir, f"trial_{trial.number}")
    best_path, val_metrics = run_training_loop(
        model=model,
        train_dataset=train_ds,
        val_dataset=val_ds,
        output_dir=output_dir,
        epochs=epochs,
        batch_size=batch_size,
        lr=lr,
        device=device,
        patience=args.patience
    )
    
    # Return validation AUC as objective to maximize
    return val_metrics['best_auc']

def main(args):
    # Create study
    study = optuna.create_study(direction="maximize")
    
    # Optimize
    study.optimize(lambda trial: objective(trial, args), n_trials=args.n_trials)
    
    # Print results
    print("Best trial:")
    trial = study.best_trial
    print(f"  Value: {trial.value}")
    print("  Params: ")
    for key, value in trial.params.items():
        print(f"    {key}: {value}")
    
    # Save study results
    study_file = os.path.join(args.output_dir, "optuna_study.json")
    with open(study_file, "w") as f:
        json.dump({
            "best_value": trial.value,
            "best_params": trial.params,
            "trials": [
                {
                    "number": t.number,
                    "value": t.value,
                    "params": t.params
                }
                for t in study.trials
            ]
        }, f, indent=2)
    
    print(f"Study results saved to {study_file}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", required=True, help="Path to dataset")
    parser.add_argument("--output_dir", default="/tmp/optuna_output", help="Output directory")
    parser.add_argument("--n_trials", type=int, default=20, help="Number of trials")
    parser.add_argument("--img_size", type=int, default=224, help="Image size")
    parser.add_argument("--val_frac", type=float, default=0.2, help="Validation fraction")
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu", help="Device to use")
    parser.add_argument("--num_classes", type=int, default=2, help="Number of classes")
    parser.add_argument("--pretrained", action="store_true", help="Use pretrained model")
    parser.add_argument("--patience", type=int, default=3, help="Early stopping patience")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()
    
    main(args)