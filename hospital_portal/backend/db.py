
from pymongo import MongoClient
import os, datetime

DB_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('MONGO_DB', 'aviothic_db')

client = MongoClient(DB_URI)
db = client[DB_NAME]
inferences = db['inferences']

def log_inference(case_id, timestamp, prediction, probabilities, gradcam_path=None, metadata=None):
    doc = {
        'case_id': case_id,
        'timestamp': timestamp or datetime.datetime.utcnow(),
        'prediction': int(prediction),
        'probabilities': probabilities,
        'gradcam_path': gradcam_path,
        'metadata': metadata or {}
    }
    res = inferences.insert_one(doc)
    return str(res.inserted_id)

def save_prediction(prediction_data):
    """Save prediction to database"""
    doc = {
        'case_id': prediction_data.get('case_id'),
        'timestamp': prediction_data.get('timestamp') or datetime.datetime.utcnow(),
        'prediction': prediction_data.get('prediction'),
        'probabilities': prediction_data.get('probabilities'),
        'model_version': prediction_data.get('model_version')
    }
    res = inferences.insert_one(doc)
    return str(res.inserted_id)

def get_history(limit=100, filters=None):
    q = filters or {}
    cur = inferences.find(q).sort('timestamp', -1).limit(limit)
    # convert ObjectId to string later in API
    return list(cur)

if __name__ == '__main__':
    print('Total records:', inferences.count_documents({}))
