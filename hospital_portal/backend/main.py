from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse, FileResponse
import os, uuid, datetime, io, base64
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from PIL import Image
from db import log_inference  # reuse existing db.py for Mongo logging

app = FastAPI()

HOSPITALS_DIR = os.environ.get('HOSPITALS_DIR','hospital_data')
os.makedirs(HOSPITALS_DIR, exist_ok=True)

@app.post('/hospital/register')
async def hospital_register(name: str = Form(...), contact: str = Form(...), email: str = Form(...)):
    # Very small example - in production store in MongoDB with validation
    hospital_id = uuid.uuid4().hex
    rec = {'hospital_id': hospital_id, 'name': name, 'contact': contact, 'email': email, 'created': datetime.datetime.utcnow()}
    # Here you would insert into hospital_profiles collection
    return JSONResponse({'status':'ok','hospital_id': hospital_id})

def create_report_pdf(patient_id, prediction, probabilities, out_path, gradcam_b64=None):
    c = canvas.Canvas(out_path, pagesize=A4)
    width, height = A4
    c.setFont('Helvetica-Bold', 16)
    c.drawString(1*inch, height-1*inch, 'Aviothic.ai — Clinical Report')
    c.setFont('Helvetica', 12)
    c.drawString(1*inch, height-1.5*inch, f'Patient ID: {patient_id}')
    c.drawString(1*inch, height-1.8*inch, f'Prediction: {prediction} | Probabilities: {probabilities}')
    if gradcam_b64:
        imgdata = base64.b64decode(gradcam_b64)
        img = Image.open(io.BytesIO(imgdata))
        img_path = out_path + '_gradcam.png'
        img.save(img_path)
        c.drawImage(img_path, 1*inch, height-6*inch, width=4*inch, preserveAspectRatio=True, mask='auto')
    c.save()

@app.post('/hospital/upload')
async def hospital_upload(hospital_id: str = Form(...), file: UploadFile = File(...)):
    contents = await file.read()
    # Basic save - in production anonymize DICOM and validate
    hid_dir = os.path.join(HOSPITALS_DIR, hospital_id)
    os.makedirs(hid_dir, exist_ok=True)
    fname = f'upload_{uuid.uuid4().hex}.png'
    fpath = os.path.join(hid_dir, fname)
    with open(fpath, 'wb') as f:
        f.write(contents)
    # Call internal /predict endpoint - here we simulate by returning dummy prediction
    # In real integration, call backend inference API or import predictor
    prediction = 1
    probabilities = [0.12, 0.88]
    # Simulate Grad-CAM b64 (empty)
    gradcam_b64 = None
    report_path = os.path.join(hid_dir, f'report_{uuid.uuid4().hex}.pdf')
    create_report_pdf('PATIENT-ANON', 'Malignant' if prediction==1 else 'Benign', probabilities, report_path, gradcam_b64)
    # Log to DB (reuse existing log_inference)
    try:
        log_id = log_inference(f'case_{uuid.uuid4().hex}', datetime.datetime.utcnow(), int(prediction), probabilities, gradcam_path=None, metadata={'hospital_id':hospital_id})
    except Exception:
        log_id = None
    return JSONResponse({'status':'ok','report_path': report_path, 'log_id': log_id})

@app.get('/hospital/report/{hospital_id}/{filename}')
async def get_report(hospital_id: str, filename: str):
    hid_dir = os.path.join(HOSPITALS_DIR, hospital_id)
    path = os.path.join(hid_dir, filename)
    if os.path.exists(path):
        return FileResponse(path, media_type='application/pdf', filename=filename)
    raise HTTPException(status_code=404, detail='Report not found')