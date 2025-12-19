# Prediction model
from sqlalchemy import Column, Integer, String, DateTime, Float
from sqlalchemy.sql import func
from ..database import Base

class Prediction(Base):
    __tablename__ = "predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String, index=True)
    image_path = Column(String)
    prediction_result = Column(Float)
    confidence = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())