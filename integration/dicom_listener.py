import logging
import os
import requests
from pynetdicom import AE, evt
from pynetdicom.sop_class import CTImageStorage, MRImageStorage, SecondaryCaptureImageStorage
from pynetdicom.sop_class import DigitalXRayImagePresentationStorage, DigitalMammographyXRayImagePresentationStorage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Backend API configuration
BACKEND_PREDICT_URL = os.environ.get("BACKEND_PREDICT_URL", "http://backend:8000/api/v1/predict")
DUMMY_TOKEN = "your_production_secret_key_here_change_this"  # Replace with actual auth header setup

def handle_store(event):
    """Event handler for C-STORE request."""
    dataset = event.dataset
    dataset.file_meta = event.file_meta

    # Ensure storage directory exists
    storage_dir = "/tmp/pacs_incoming"
    os.makedirs(storage_dir, exist_ok=True)
    
    # Save the DICOM file
    sop_uid = dataset.SOPInstanceUID
    file_path = os.path.join(storage_dir, f"{sop_uid}.dcm")
    dataset.save_as(file_path, write_like_original=False)
    
    logger.info(f"Received and saved DICOM file: {file_path}")
    
    # Automatically route to the Inference API
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (f"{sop_uid}.dcm", f, 'application/dicom')}
            headers = {"Authorization": f"Bearer {DUMMY_TOKEN}"}
            # Add an artificial user for the listener mapping if needed
            response = requests.post(BACKEND_PREDICT_URL, files=files, headers=headers)
        
        if response.status_code == 200:
            logger.info(f"Successfully processed by AI Pipeline. ID: {response.json().get('id')}")
        else:
            logger.error(f"Failed AI Pipeline processing. Status: {response.status_code}, {response.text}")
    except Exception as e:
        logger.error(f"Failed connecting to AI API: {e}")

    # Clean up
    if os.path.exists(file_path):
        os.remove(file_path)

    # Return 'Success' status
    return 0x0000

def start_listener(port=11112):
    """Start the DICOM Listener serving C-STORE."""
    ae = AE(ae_title=b'AVIOTHIC_AI')

    # Add the supported presentation contexts
    ae.add_supported_context(CTImageStorage)
    ae.add_supported_context(MRImageStorage)
    ae.add_supported_context(SecondaryCaptureImageStorage)
    ae.add_supported_context(DigitalXRayImagePresentationStorage)
    ae.add_supported_context(DigitalMammographyXRayImagePresentationStorage)

    handlers = [(evt.EVT_C_STORE, handle_store)]

    logger.info(f"Starting DICOM Listener on port {port}...")
    # Start listening for incoming association requests
    ae.start_server(("", port), evt_handlers=handlers)

if __name__ == "__main__":
    start_listener()
