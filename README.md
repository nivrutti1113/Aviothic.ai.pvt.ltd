# Aviothic.ai — Phase 3 Completion Package

This package contains the deliverables requested to complete Phase 3 and prepare for hospital onboarding and pilots.

## Files Included

1. `Clinical_Pilot_Report_Template.pdf` - Regulatory package PDF (Model Card, DPIA, Risk Assessment, Security Design)
2. `hospital_portal/` - Frontend + backend starter code for hospital onboarding
3. `mlflow_watcher.py` - Drift detection and auto-retrain watcher
4. `compliance/` - Security audit GitHub Actions + SBOM script
5. `retrain_package/` - Complete retraining package with extended capabilities

## Component Details

### Hospital Portal (`hospital_portal/`)

#### Backend (`hospital_portal/backend/`)
- `main.py`: FastAPI endpoints for hospital registration and image upload
  - `/hospital/register`: Register new hospitals with name, contact, and email
  - `/hospital/upload`: Process medical images and generate reports
  - `/hospital/report/{hospital_id}/{filename}`: Serve generated PDF reports

#### Frontend (`hospital_portal/frontend/`)
- `HospitalOnboard.js`: React component for hospital registration
- `HospitalUpload.js`: React component for medical image upload

### Retraining Package (`retrain_package/`)

Complete machine learning pipeline with:
- `retrain.py`: Main retraining driver with ClinicalDataset and trainer
- `validate.py`: Model validation against AUC thresholds
- `dataset.py`: ClinicalDataset implementation for medical images
- `trainer.py`: Training loop and model building (EfficientNet-B0)
- `tune_optuna.py`: Hyperparameter optimization using Optuna
- `convert_ddsm.py`: CBIS-DDSM DICOM parser and converter
- `mlflow_s3_integration.py`: MLflow integration with S3 storage
- `train_gpu.yml`: GitHub Actions workflow for GPU training
- `requirements-train.txt`: Training dependencies

### Drift Detection (`mlflow_watcher.py`)

Monitors production model performance and triggers retraining when AUC falls below threshold:
- Polls MLflow for latest production model metrics
- Triggers retrain via GitHub repository dispatch when performance degrades
- Configurable AUC threshold and polling interval

### Compliance (`compliance/`)

Security and compliance tools:
- `security_audit.yml`: GitHub Actions workflow for security scanning with Trivy
- `generate_sbom.sh`: Script to generate Software Bill of Materials

## Setup Instructions

### Hospital Portal

1. Backend:
   ```bash
   cd hospital_portal/backend
   pip install fastapi uvicorn python-multipart reportlab pillow
   uvicorn main:app --reload
   ```

2. Frontend:
   ```bash
   cd hospital_portal/frontend
   # Integrate components into your React application
   ```

### Retraining Package

1. Install dependencies:
   ```bash
   cd retrain_package
   pip install -r training/requirements-train.txt
   ```

2. Run training:
   ```bash
   python training/retrain.py --data_dir /path/to/data --output_dir /path/to/output
   ```

3. Hyperparameter tuning:
   ```bash
   python training/tune_optuna.py --data_dir /path/to/data --output_dir /path/to/output
   ```

### Drift Detection

1. Set environment variables:
   ```bash
   export MLFLOW_TRACKING_URI=your_mlflow_uri
   export MODEL_NAME=Aviothic_Breast_Model
   export MIN_AUC=0.95
   export GITHUB_REPO=your/repo
   export GITHUB_TOKEN=your_token
   ```

2. Run watcher:
   ```bash
   python mlflow_watcher.py
   ```

## Deployment

All components are designed to work with cloud infrastructure:
- Hospital portal can be deployed to any cloud provider
- Retraining package supports GPU acceleration
- MLflow watcher integrates with GitHub Actions
- Compliance tools work with GitHub Actions for automated security scanning

## Notes

This package completes Phase 3 requirements and prepares the system for clinical pilot studies and hospital onboarding.