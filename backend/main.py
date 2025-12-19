# backend/app/main.py
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse, FileResponse
import uvicorn
import io
from PIL import Image
import torch
import torchvision.transforms as T
import numpy as np
import base64
import os
import uuid
from datetime import datetime

# Import local modules
from gradcam import generate_gradcam
from report import generate_report
from db import save_prediction, get_history

app = FastAPI(title="Aviothic.ai Inference API")

# In-memory storage for demo purposes
predictions_db = []

# load model (PyTorch stub)
MODEL_PATH = "app/models/model.pt"
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = None
try:
    model = torch.load(MODEL_PATH, map_location=device)
    model.eval()
except Exception as e:
    print("Model load failed:", e)

transform = T.Compose([
    T.Resize((224,224)),
    T.Grayscale(num_output_channels=3),  # if single-channel convert
    T.ToTensor(),
    T.Normalize(mean=[0.485,0.456,0.406], std=[0.229,0.224,0.225])
])

@app.get("/")
async def root():
    return {"status": "Aviothic backend running"}

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    contents = await file.read()
    image = Image.open(io.BytesIO(contents)).convert("RGB")
    x = transform(image).unsqueeze(0).to(device)
    if model is None:
        return JSONResponse({"error":"model not loaded"}, status_code=503)
    with torch.no_grad():
        logits = model(x)
        probs = torch.softmax(logits, dim=1).cpu().numpy().tolist()[0]
        pred = int(np.argmax(probs))
    
    # Generate case ID
    case_id = str(uuid.uuid4())[:8]
    
    # Prepare result
    result = {
        "case_id": case_id,
        "prediction": int(pred),
        "probabilities": probs,
        "timestamp": datetime.now().isoformat(),
        "model_version": "v1.0"
    }
    
    # Save to database
    save_prediction(result)
    
    # Store in memory for demo
    predictions_db.append(result)
    
    return result

@app.post("/gradcam")
async def gradcam(file: UploadFile = File(...)):
    contents = await file.read()
    image = Image.open(io.BytesIO(contents)).convert("RGB")
    mask_b64 = generate_gradcam(model, image, transform)
    return {"gradcam_base64": mask_b64}

@app.get("/history")
async def history():
    # Return prediction history
    return predictions_db

@app.get("/report/{case_id}")
async def get_report(case_id: str):
    # Find the prediction by case_id
    prediction = None
    for p in predictions_db:
        if p["case_id"] == case_id:
            prediction = p
            break
    
    if not prediction:
        return {"error": "Report not found"}
    
    # Generate PDF report
    output_path = f"app/static/report_{case_id}.pdf"
    generate_report(
        output_path=output_path,
        patient_id="PATIENT123",
        prediction=str(prediction["prediction"]),
        probabilities=prediction["probabilities"],
        gradcam_b64=None
    )
    
    # Return the PDF file
    if os.path.exists(output_path):
        return FileResponse(output_path, media_type='application/pdf', filename=f"report_{case_id}.pdf")
    else:
        return {"error": "Report generation failed"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
