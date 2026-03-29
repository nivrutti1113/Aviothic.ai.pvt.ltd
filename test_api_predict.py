import requests
import os
import json

# Configuration
API_URL = "http://localhost:8000/predict"
IMAGE_PATH = "sample_mammo.png" # Provide a real file path for testing

def test_api_prediction():
    if not os.path.exists(IMAGE_PATH):
        print(f"\u26a0\ufe0f  Local sample file {IMAGE_PATH} not found. Skipped.")
        return

    print(f"\ud83c\udfaf Sending {IMAGE_PATH} to AI Screening System...")
    
    with open(IMAGE_PATH, 'rb') as f:
        files = {'file': (os.path.basename(IMAGE_PATH), f, 'application/octet-stream')}
        # Mock auth for doctor if needed (depends on your JWT setup)
        # headers = {"Authorization": "Bearer YOUR_JWT_TOKEN"}
        response = requests.post(API_URL, files=files)

    if response.status_code == 200:
        print("\u2705 Prediction Successful!")
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"\u274c Prediction Failed with status code {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    test_api_prediction()
