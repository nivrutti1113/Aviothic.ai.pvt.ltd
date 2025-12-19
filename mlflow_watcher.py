#!/usr/bin/env python3
"""mlflow_watcher.py
Simple watcher that polls MLflow for latest production model metrics and triggers retrain via repository_dispatch
if AUC falls below threshold. This is a template - configure with your MLflow and GitHub tokens.
"""
import os, time, requests, json
from mlflow.tracking import MlflowClient

MLFLOW_URI = os.environ.get('MLFLOW_TRACKING_URI')
MODEL_NAME = os.environ.get('MODEL_NAME','Aviothic_Breast_Model')
MIN_AUC = float(os.environ.get('MIN_AUC','0.95'))
GITHUB_REPO = os.environ.get('GITHUB_REPO')  # e.g. user/repo
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')

client = MlflowClient(tracking_uri=MLFLOW_URI)

def get_production_model_auc():
    # Find latest production model version and its run metrics
    try:
        versions = client.get_latest_versions(name=MODEL_NAME, stages=['Production'])
        if not versions:
            return None, None
        v = versions[0]
        run = client.get_run(v.run_id)
        metrics = run.data.metrics
        auc = float(metrics.get('best_auc') or metrics.get('val_auc') or 0.0)
        return auc, v.version
    except Exception as e:
        print('Error fetching model info:', e)
        return None, None

def trigger_retrain(payload):
    url = f'https://api.github.com/repos/{GITHUB_REPO}/dispatches'
    headers = {'Authorization': f'token {GITHUB_TOKEN}', 'Accept': 'application/vnd.github.everest-preview+json'}
    data = {'event_type': 'retrain-request', 'client_payload': payload}
    r = requests.post(url, headers=headers, data=json.dumps(data))
    print('Triggered retrain, status', r.status_code, r.text)
    return r.status_code

if __name__ == '__main__':
    while True:
        auc, version = get_production_model_auc()
        print('Current production AUC:', auc, 'version:', version)
        if auc is not None and auc < MIN_AUC:
            print('AUC below threshold, triggering retrain...')
            payload = {'reason':'drift_detected','current_auc':auc, 'version': version}
            if os.environ.get('GITHUB_REPO') and os.environ.get('GITHUB_TOKEN'):
                trigger_retrain(payload)
            else:
                print('GITHUB_REPO or GITHUB_TOKEN not set; cannot trigger retrain automatically.')
        time.sleep(3600)  # check every hour