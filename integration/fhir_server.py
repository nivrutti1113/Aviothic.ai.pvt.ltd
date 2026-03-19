from fastapi import FastAPI, HTTPException, Request, Response
from fhir.resources.patient import Patient
from fhir.resources.observation import Observation
from fhir.resources.servicerequest import ServiceRequest
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Aviothic AI FHIR Interface")

@app.post("/fhir/Patient")
async def create_patient(request: Request):
    """Ingest a new Patient via FHIR Protocol."""
    try:
        data = await request.json()
        patient = Patient.parse_obj(data)
        logger.info(f"Ingested FHIR Patient: {patient.id}")
        # Insert database logic here to align patient.id with local DB
        return Response(status_code=201, headers={"Location": f"/fhir/Patient/{patient.id}"})
    except Exception as e:
        logger.error(f"Failed to parse FHIR Patient: {e}")
        raise HTTPException(status_code=400, detail="Invalid FHIR Patient resource")

@app.get("/fhir/Patient/{patient_id}")
async def get_patient(patient_id: str):
    """Retrieve Patient by ID."""
    # Stub reading from DB
    patient = Patient(id=patient_id, active=True)
    return Response(content=patient.json(), media_type="application/fhir+json")

@app.post("/fhir/ServiceRequest")
async def receive_order(request: Request):
    """Ingest a ServiceRequest (Order) from HL7/FHIR EHR."""
    try:
        data = await request.json()
        order = ServiceRequest.parse_obj(data)
        logger.info(f"Received Order: {order.id} for Subject: {order.subject.reference}")
        # Process order logic: Update AI scheduling 
        return Response(status_code=201, headers={"Location": f"/fhir/ServiceRequest/{order.id}"})
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid FHIR ServiceRequest resource")

@app.post("/fhir/Observation")
async def create_observation(request: Request):
    """Optionally return an AI result as an observation back to the hospital."""
    try:
        data = await request.json()
        obs = Observation.parse_obj(data)
        logger.info(f"Created Observation Result: {obs.id}")
        return Response(status_code=201)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid FHIR Observation resource")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
