#!/usr/bin/env python3
"""training/mlflow_s3_integration.py
MLflow S3 integration for artifact storage.
"""
import os
import boto3
import mlflow
from mlflow.tracking import MlflowClient

def setup_mlflow_s3(bucket_name, aws_access_key_id=None, aws_secret_access_key=None, region_name='us-east-1'):
    """Setup MLflow to use S3 for artifact storage."""
    
    # Set AWS credentials if provided
    if aws_access_key_id:
        os.environ['AWS_ACCESS_KEY_ID'] = aws_access_key_id
    if aws_secret_access_key:
        os.environ['AWS_SECRET_ACCESS_KEY'] = aws_secret_access_key
    
    # Create S3 bucket if it doesn't exist
    s3_client = boto3.client('s3', region_name=region_name)
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        print(f"S3 bucket {bucket_name} already exists")
    except:
        print(f"Creating S3 bucket {bucket_name}")
        if region_name == 'us-east-1':
            s3_client.create_bucket(Bucket=bucket_name)
        else:
            s3_client.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={'LocationConstraint': region_name}
            )
    
    # Configure MLflow to use S3
    artifact_uri = f"s3://{bucket_name}/mlflow-artifacts"
    os.environ['MLFLOW_S3_ENDPOINT_URL'] = f"https://s3.{region_name}.amazonaws.com"
    os.environ['MLFLOW_S3_BUCKET'] = bucket_name
    
    print(f"MLflow configured to use S3 bucket {bucket_name} for artifacts")
    return artifact_uri

def log_model_to_s3(model, model_name, run_id=None, bucket_name=None):
    """Log model to S3 using MLflow."""
    # Setup MLflow tracking URI if not already set
    if not os.environ.get('MLFLOW_TRACKING_URI'):
        mlflow.set_tracking_uri("sqlite:///mlflow.db")
    
    # Start or continue run
    if run_id:
        mlflow.start_run(run_id=run_id)
    elif not mlflow.active_run():
        mlflow.start_run()
    
    # Log model
    with mlflow.start_run(nested=True):
        mlflow.pytorch.log_model(model, model_name, conda_env={
            'name': 'model_env',
            'channels': ['defaults'],
            'dependencies': [
                'python=3.8',
                'pytorch',
                'torchvision',
                'numpy',
                'pillow'
            ]
        })
    
    # Get model URI
    model_uri = f"runs:/{mlflow.active_run().info.run_id}/{model_name}"
    print(f"Model logged to: {model_uri}")
    
    return model_uri

def register_model_from_s3(model_uri, model_name, stage="Production"):
    """Register model from S3 in MLflow Model Registry."""
    client = MlflowClient()
    
    try:
        # Create registered model if it doesn't exist
        client.create_registered_model(model_name)
        print(f"Created registered model: {model_name}")
    except:
        print(f"Registered model {model_name} already exists")
    
    # Create model version
    model_version = client.create_model_version(
        name=model_name,
        source=model_uri,
        run_id=mlflow.active_run().info.run_id if mlflow.active_run() else None
    )
    
    print(f"Created model version: {model_version.version}")
    
    # Transition to desired stage
    client.transition_model_version_stage(
        name=model_name,
        version=model_version.version,
        stage=stage
    )
    
    print(f"Model version {model_version.version} transitioned to {stage}")
    return model_version

def main():
    """Example usage of MLflow S3 integration."""
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--bucket_name", required=True, help="S3 bucket name")
    parser.add_argument("--aws_access_key_id", help="AWS Access Key ID")
    parser.add_argument("--aws_secret_access_key", help="AWS Secret Access Key")
    parser.add_argument("--region_name", default="us-east-1", help="AWS region")
    args = parser.parse_args()
    
    # Setup MLflow with S3
    artifact_uri = setup_mlflow_s3(
        args.bucket_name,
        args.aws_access_key_id,
        args.aws_secret_access_key,
        args.region_name
    )
    
    print(f"MLflow S3 integration configured with artifact URI: {artifact_uri}")

if __name__ == "__main__":
    main()