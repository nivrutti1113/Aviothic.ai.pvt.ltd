#!/usr/bin/env python3
"""training/promote_model.py
Simple MLflow model promotion helper. Assumes model version exists in registry.
"""
import argparse, mlflow

def promote(run_id, stage='staging'):
    client = mlflow.tracking.MlflowClient()
    print(f"Request to promote run {run_id} to stage {stage}")
    # This is a placeholder for real MLflow registry promotion logic

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--run_id', required=True)
    p.add_argument('--stage', default='staging')
    args = p.parse_args()
    promote(args.run_id, args.stage)